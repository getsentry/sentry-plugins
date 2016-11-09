from __future__ import absolute_import

from sentry.plugins.bases.notify import NotifyPlugin

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.utils import get_secret_field_config

from .client import PushoverClient


class PushoverPlugin(CorePluginMixin, NotifyPlugin):
    slug = 'pushover'
    title = 'Pushover'
    conf_title = 'Pushover'
    conf_key = 'pushover'

    def is_configured(self, project):
        return all(
            self.get_option(key, project)
            for key in ('userkey', 'apikey')
        )

    def get_config(self, **kwargs):
        userkey = self.get_option('userkey', kwargs['project'])
        apikey = self.get_option('apikey', kwargs['project'])
        userkey_field = get_secret_field_config(userkey,
                                                'Your user key. See https://pushover.net/',
                                                include_prefix=True)
        userkey_field.update({
            'name': 'userkey',
            'label': 'User Key'
        })

        apikey_field = get_secret_field_config(apikey,
                                               'Application API token. See https://pushover.net/apps/',
                                               include_prefix=True)

        apikey_field.update({
            'name': 'apikey',
            'label': 'API Key'
        })
        return [userkey_field, apikey_field, {
            'name': 'priority',
            'label': 'Message Priority',
            'type': 'choice',
            'required': True,
            'choices': [
                ('-2', 'Lowest'),
                ('-1', 'Low'),
                ('0', 'Normal'),
                ('1', 'High'),
                ('2', 'Emergency'),
            ],
            'default': '0',
        }]

    def get_client(self, project):
        return PushoverClient(
            apikey=self.get_option('apikey', project),
            userkey=self.get_option('userkey', project),
        )

    def notify(self, notification):
        event = notification.event
        group = event.group
        project = group.project

        title = '%s: %s' % (project.name, group.title)
        link = group.get_absolute_url()

        message = event.get_legacy_message()[:256]

        tags = event.get_tags()
        if tags:
            message += '\n\nTags: %s' % (', '.join(
                '%s=%s' % (k, v) for (k, v) in tags))

        client = self.get_client(project)
        response = client.send_message({
            'message': message[:1024],
            'title': title[:250],
            'url': link,
            'url_title': 'Issue Details',
            'priority': int(self.get_option('priority', project) or 0),
        })
        assert response['status']
