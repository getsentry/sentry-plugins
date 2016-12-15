"""
- Turn on HTTP Event Collector by enabling its endpoint. HEC is not enabled by default.
  - http://dev.splunk.com/view/event-collector/SP-CAAAE7F
  - Settings > Data Inputs > HTTP Event Collector > Add new
    - Name: Sentry
  - You'll be given an HEC token, which is needed to configure Sentry.
- On the client that will log to HEC, create a POST request, and set its authentication header or key/value pair to include the HEC token.
- POST data to the HEC token receiver.

Note: Managed Splunk Cloud customers can turn on HTTP Event Collector by filing a request ticket with Splunk Support.
Note: Managed Splunk Cloud customers can create a HEC token by filing a request ticket with Splunk Support.

For more details on the payload: http://dev.splunk.com/view/event-collector/SP-CAAAE6M
"""

from __future__ import absolute_import

from sentry import http
from sentry.app import ratelimiter
from sentry.plugins.base import Plugin
from sentry.plugins.base.configuration import react_plugin_config
from sentry.utils.hashlib import md5_text

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.utils import get_secret_field_config


class SplunkPlugin(CorePluginMixin, Plugin):
    title = 'Splunk'
    slug = 'splunk'
    description = 'Send Sentry events into Splunk.'
    conf_key = 'splunk'

    def configure(self, project, request):
        return react_plugin_config(self, project, request)

    def has_project_conf(self):
        return True

    def get_plugin_type(self):
        return 'data-forwarding'

    def get_config(self, project, **kwargs):
        return [{
            'name': 'instance',
            'label': 'Instance URL',
            'type': 'url',
            'required': True,
            'help': 'The URL to your HEC Splunk instance.',
            'placeholder': 'e.g. https://my-splunk.example.com:8088',
        }, {
            'name': 'index',
            'label': 'Index',
            'type': 'string',
            'required': True,
            'default': 'main',
        }, {
            'name': 'source',
            'label': 'Source',
            'type': 'string',
            'required': True,
            'default': 'sentry',
        }, get_secret_field_config(
            name='token',
            label='Token',
            secret=self.get_option('token', project),
        )]

    def get_host_for_splunk(self, event):
        host = event.get_tag('server_name')
        if host:
            return host

        user_interface = event.interfaces.get('sentry.interfaces.User')
        if user_interface:
            host = user_interface.ip_address
            if host:
                return host

        return None

    def get_event_payload(self, event):
        props = {
            'event_id': event.event_id,
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
                'request_url': http.url,
                'request_method': http.method,
                'request_referer': headers.get('Referer', ''),
            })
        if 'sentry.interfaces.Exception' in event.interfaces:
            exc = event.interfaces['sentry.interfaces.Exception'].values[0]
            props.update({
                'exception_type': exc.type,
                'exception_value': exc.value,
            })
        elif 'sentry.interfaces.Message' in event.interfaces:
            msg = event.interfaces['sentry.interfaces.Message']
            props.update({
                'message': msg.formatted or msg.message,
            })
        return props

    # http://dev.splunk.com/view/event-collector/SP-CAAAE6M
    def post_process(self, event, **kwargs):
        token = self.get_option('token', event.project)
        index = self.get_option('index', event.project)
        instance = self.get_option('instance', event.project)
        if not (token and index and instance):
            return

        if not instance.endswith('/services/collector'):
            instance = instance.rstrip('/') + '/services/collector'

        source = self.get_option('source', event.project) or 'sentry'

        rl_key = 'splunk:{}'.format(md5_text(token).hexdigest())
        # limit splunk to 50 requests/second
        if ratelimiter.is_limited(rl_key, limit=50, window=1):
            return

        payload = {
            'time': int(event.datetime.strftime('%s')),
            'source': source,
            'index': index,
            'event': self.get_event_payload(event),
        }
        host = self.get_host_for_splunk(event)
        if host:
            payload['host'] = host

        session = http.build_session()
        session.post(
            instance,
            json=payload,
            # Splunk cloud instances certifcates dont play nicely
            verify=False,
            headers={
                'Authorization': 'Splunk {}'.format(token)
            },
        ).raise_for_status()
