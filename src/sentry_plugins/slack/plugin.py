from __future__ import absolute_import

import operator

from django.core.urlresolvers import reverse
from django.db.models import Q
from sentry import http
from sentry.models import TagKey, TagValue
from sentry.plugins.bases import notify
from sentry.utils import json
from sentry.utils.http import absolute_uri

from sentry_plugins.base import CorePluginMixin

LEVEL_TO_COLOR = {
    'debug': 'cfd3da',
    'info': '2788ce',
    'warning': 'f18500',
    'error': 'f43f20',
    'fatal': 'd20f2a',
}


class SlackPlugin(CorePluginMixin, notify.NotificationPlugin):
    title = 'Slack'
    slug = 'slack'
    description = 'Post notifications to a Slack channel.'
    conf_key = 'slack'

    def is_configured(self, project):
        return bool(self.get_option('webhook', project))

    def get_config(self, project, **kwargs):
        return [{
            'name': 'webhook',
            'label': 'Webhook URL',
            'type': 'url',
            'placeholder': 'e.g. https://hooks.slack.com/services/000000000/000000000/00000000000000000',
            'required': True,
            'help': 'Your custom Slack webhook URL.'
        }, {
            'name': 'username',
            'label': 'Bot Name',
            'type': 'string',
            'placeholder': 'e.g. Sentry',
            'default': 'Sentry',
            'required': False,
            'help': 'The name used when publishing messages.'
        }, {
            'name': 'icon_url',
            'label': 'Icon URL',
            'type': 'url',
            'required': False,
            'help': (
                'The url of the icon to appear beside your bot (32px png), '
                'leave empty for none.<br />You may use '
                'http://myovchev.github.io/sentry-slack/images/logo32.png'
            ),
        }, {
            'name': 'channel',
            'label': 'Destination',
            'type': 'string',
            'placeholder': 'e.g. #engineering',
            'required': False,
            'help': 'Optional #channel name or @user',
        }, {
            'name': 'include_tags',
            'label': 'Include Tags',
            'type': 'bool',
            'required': False,
            'help': 'Include tags with notifications',
        }, {
            'name': 'included_tag_keys',
            'label': 'Included Tags',
            'type': 'string',
            'required': False,
            'help': (
                'Only include these tags (comma separated list). '
                'Leave empty to include all.'
            ),
        }, {
            'name': 'excluded_tag_keys',
            'label': 'Excluded Tags',
            'type': 'string',
            'required': False,
            'help': 'Exclude these tags (comma separated list).',
        }, {
            'name': 'include_rules',
            'label': 'Include Rules',
            'type': 'bool',
            'required': False,
            'help': 'Include triggering rules with notifications.',
        }]

    def color_for_event(self, event):
        return '#' + LEVEL_TO_COLOR.get(event.get_tag('level'), 'error')

    def _get_tags(self, event):
        # TODO(dcramer): we want this behavior to be more accessible in sentry
        tag_list = event.get_tags()
        if not tag_list:
            return ()

        key_labels = {
            o.key: o.get_label()
            for o in TagKey.objects.filter(
                project=event.project,
                key__in=[t[0] for t in tag_list],
            )
        }
        value_labels = {
            (o.key, o.value): o.get_label()
            for o in TagValue.objects.filter(
                reduce(operator.or_, (Q(key=k, value=v) for k, v in tag_list)),
                project=event.project,
            )
        }
        return (
            (key_labels.get(k, k), value_labels.get((k, v), v))
            for k, v in tag_list
        )

    def get_tag_list(self, name, project):
        option = self.get_option(name, project)
        if not option:
            return None
        return set(tag.strip().lower() for tag in option.split(','))

    def notify(self, notification):
        event = notification.event
        group = event.group
        project = group.project

        if not self.is_configured(project):
            return

        webhook = self.get_option('webhook', project)
        username = (self.get_option('username', project) or 'Sentry').strip()
        icon_url = self.get_option('icon_url', project)
        channel = (self.get_option('channel', project) or '').strip()

        title = event.message_short.encode('utf-8')
        # TODO(dcramer): we'd like this to be the event culprit, but Sentry
        # does not currently retain it
        if group.culprit:
            culprit = group.culprit.encode('utf-8')
        else:
            culprit = None
        project_name = project.get_full_name().encode('utf-8')

        fields = []

        # They can be the same if there is no culprit
        # So we set culprit to an empty string instead of duplicating the text
        if culprit and title != culprit:
            fields.append({
                'title': 'Culprit',
                'value': culprit,
                'short': False,
            })

        fields.append({
            'title': 'Project',
            'value': project_name,
            'short': True,
        })

        if self.get_option('include_rules', project):
            rules = []
            for rule in notification.rules:
                rule_link = reverse('sentry-edit-project-rule', args=[
                    group.organization.slug, project.slug, rule.id
                ])
                # Make sure it's an absolute uri since we're sending this
                # outside of Sentry into Slack
                rule_link = absolute_uri(rule_link)
                rules.append((rule_link, rule.label.encode('utf-8')))

            if rules:
                fields.append({
                    'title': 'Triggered By',
                    'value': ', '.join('<%s | %s>' % r for r in rules),
                    'short': False,
                })

        if self.get_option('include_tags', project):
            included_tags = set(self.get_tag_list('included_tag_keys', project) or [])
            excluded_tags = set(self.get_tag_list('excluded_tag_keys', project) or [])
            for tag_key, tag_value in self._get_tags(event):
                key = tag_key.lower()
                std_key = TagKey.get_standardized_key(key)
                if included_tags and key not in included_tags and std_key not in included_tags:
                    continue
                if excluded_tags and (key in excluded_tags or std_key in excluded_tags):
                    continue
                fields.append({
                    'title': tag_key.encode('utf-8'),
                    'value': tag_value.encode('utf-8'),
                    'short': True,
                })

        payload = {
            'parse': 'none',
            'attachments': [{
                'fallback': '[%s] %s' % (project_name, title),
                'title': title,
                'title_link': group.get_absolute_url(),
                'color': self.color_for_event(event),
                'fields': fields,
            }]
        }

        if username:
            payload['username'] = username.encode('utf-8')

        if channel:
            payload['channel'] = channel

        if icon_url:
            payload['icon_url'] = icon_url

        values = {'payload': json.dumps(payload)}

        # Apparently we've stored some bad data from before we used `URLField`.
        webhook = webhook.strip(' ')
        return http.safe_urlopen(webhook, method='POST', data=values)
