from __future__ import absolute_import

from sentry.plugins.bases.notify import NotifyPlugin
from sentry.utils.http import absolute_uri

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.utils import get_secret_field_config

from .client import PagerDutyClient


class PagerDutyPlugin(CorePluginMixin, NotifyPlugin):
    description = 'Send alerts to PagerDuty.'
    slug = 'pagerduty'
    title = 'PagerDuty'
    conf_key = slug
    conf_title = title

    def is_configured(self, project, **kwargs):
        return bool(self.get_option('service_key', project))

    def get_config(self, **kwargs):
        service_key = self.get_option('service_key', kwargs['project'])
        secret_field = get_secret_field_config(service_key,
                                               'PagerDuty\'s Sentry service Integration Key',
                                               include_prefix=True)
        secret_field.update({
            'name': 'service_key',
            'label': 'Service Key'
        })
        return [secret_field]

    def get_client(self, project):
        return PagerDutyClient(
            service_key=self.get_option('service_key', project),
        )

    def notify_users(self, group, event, fail_silently=False):
        if not self.is_configured(group.project):
            return

        description = event.get_legacy_message()[:1024]

        details = {
            'event_id': event.event_id,
            'project': group.project.name,
            'release': event.get_tag('sentry:release'),
            'platform': event.platform,
            'culprit': event.culprit,
            'datetime': event.datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'tags': dict(event.get_tags()),
            'url': group.get_absolute_url(),
        }

        client = self.get_client(group.project)
        response = client.trigger_incident(
            description=description,
            event_type='trigger',
            incident_key=group.id,
            details=details,
            contexts=[{
                'type': 'link',
                'href': absolute_uri(group.get_absolute_url()),
                'text': 'Issue Details',
            }],
        )
        assert response['status'] == 'success'
