from __future__ import absolute_import

from sentry.plugins.bases.notify import NotifyPlugin
from sentry.utils.http import absolute_uri

from sentry_plugins.base import CorePluginMixin

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
        return [{
            'name': 'service_key',
            'label': 'Service Key',
            'type': 'secret',
            'required': True,
            'help': 'PagerDuty\'s Sentry service Integration Key',
        }]

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
