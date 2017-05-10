from __future__ import absolute_import

from sentry import http
from sentry.app import ratelimiter
from sentry.plugins.base import Plugin
from sentry.plugins.base.configuration import react_plugin_config
from sentry.utils.hashlib import md5_text

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.utils import get_secret_field_config


class SegmentPlugin(CorePluginMixin, Plugin):
    title = 'Segment'
    slug = 'segment'
    description = 'Send Sentry events into Segment.'
    conf_key = 'segment'

    endpoint = 'https://api.segment.io/v1/track'

    def configure(self, project, request):
        return react_plugin_config(self, project, request)

    def has_project_conf(self):
        return True

    def get_plugin_type(self):
        return 'data-forwarding'

    def get_config(self, project, **kwargs):
        return [
            get_secret_field_config(
                name='write_key',
                label='Write Key',
                secret=self.get_option('write_key', project),
                help_text='Your Segment write key',
            ),
        ]

    def get_event_props(self, event):
        props = {
            'eventId': event.event_id,
            'transaction': event.get_tag('transaction') or '',
            'release': event.get_tag('sentry:release') or '',
            'environment': event.get_tag('environment') or '',
        }
        if 'sentry.interfaces.Http' in event.interfaces:
            http = event.interfaces['sentry.interfaces.Http']
            headers = http.headers
            if not isinstance(headers, dict):
                headers = dict(headers or ())

            props.update({
                'requestUrl': http.url,
                'requestMethod': http.method,
                'requestReferer': headers.get('Referer', ''),
            })
        if 'sentry.interfaces.Exception' in event.interfaces:
            exc = event.interfaces['sentry.interfaces.Exception'].values[0]
            props.update({
                'exceptionType': exc.type,
            })
        return props

    # https://segment.com/docs/spec/track/
    def get_event_payload(self, event):
        context = {
            'library': {
                'name': 'sentry',
                'version': self.version,
            },
        }

        props = {
            'eventId': event.event_id,
            'transaction': event.get_tag('transaction') or '',
            'release': event.get_tag('sentry:release') or '',
            'environment': event.get_tag('environment') or '',
        }

        if 'sentry.interfaces.User' in event.interfaces:
            user = event.interfaces['sentry.interfaces.User']
            if user.ip_address:
                context['ip'] = user.ip_address
            user_id = user.id
        else:
            user_id = None

        if 'sentry.interfaces.Http' in event.interfaces:
            http = event.interfaces['sentry.interfaces.Http']
            headers = http.headers
            if not isinstance(headers, dict):
                headers = dict(headers or ())

            context.update({
                'userAgent': headers.get('User-Agent', ''),
                'page': {
                    'url': http.url,
                    'method': http.method,
                    'search': http.query_string or '',
                    'referrer': headers.get('Referer', ''),
                },
            })

        if 'sentry.interfaces.Exception' in event.interfaces:
            exc = event.interfaces['sentry.interfaces.Exception'].values[0]
            props.update({
                'exceptionType': exc.type,
            })

        return {
            'context': context,
            'userId': user_id,
            'event': 'Error Captured',
            'properties': props,
            'integration': {
                'name': 'sentry',
                'version': self.version,
            },
            'timestamp': event.datetime.isoformat() + 'Z',
        }

    def post_process(self, event, **kwargs):
        # TODO(dcramer): we currently only support authenticated events, as the
        # value of anonymous errors/crashes/etc is much less meaningful in the
        # context of Segment

        # we avoid instantiating interfaces here as they're only going to be
        # used if there's a User present
        user_interface = event.data.get('sentry.interfaces.User')
        if not user_interface:
            return

        # we currently only support errors
        if event.get_event_type() != 'error':
            return

        user_id = user_interface.get('id')

        if not user_id:
            return

        write_key = self.get_option('write_key', event.project)
        if not write_key:
            return

        rl_key = 'segment:{}'.format(md5_text(write_key).hexdigest())
        # limit segment to 50 requests/second
        if ratelimiter.is_limited(rl_key, limit=50, window=1):
            return

        payload = self.get_event_payload(event)
        session = http.build_session()
        session.post(self.endpoint, json=payload, auth=(write_key, ''))
