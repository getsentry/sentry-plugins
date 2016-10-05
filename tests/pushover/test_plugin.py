from __future__ import absolute_import

import responses

from exam import fixture
from sentry.models import Rule
from sentry.plugins import Notification
from sentry.testutils import TestCase
from six.moves.urllib.parse import parse_qs

from sentry_plugins.pushover.plugin import PushoverPlugin

SUCCESS = """{"status":1,"request":"e460545a8b333d0da2f3602aff3133d6"}"""


class PushoverPluginTest(TestCase):
    @fixture
    def plugin(self):
        return PushoverPlugin()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'pushover'

    def test_is_configured(self):
        assert self.plugin.is_configured(self.project) is False
        self.plugin.set_option('apikey', 'abcdef', self.project)
        assert self.plugin.is_configured(self.project) is False
        self.plugin.set_option('userkey', 'abcdef', self.project)
        assert self.plugin.is_configured(self.project) is True

    @responses.activate
    def test_simple_notification(self):
        responses.add('POST', 'https://api.pushover.net/1/messages.json',
                      body=SUCCESS)
        self.plugin.set_option('userkey', 'abcdef', self.project)
        self.plugin.set_option('apikey', 'ghijkl', self.project)

        group = self.create_group(message='Hello world', culprit='foo.bar')
        event = self.create_event(
            group=group, message='Hello world',
            tags={'level': 'warning'},
        )

        rule = Rule.objects.create(project=self.project, label='my rule')

        notification = Notification(event=event, rule=rule)

        with self.options({'system.url-prefix': 'http://example.com'}):
            self.plugin.notify(notification)

        request = responses.calls[0].request
        payload = parse_qs(request.body)
        assert payload == {
            'message': ['{}\n\nTags: level=warning'.format(event.get_legacy_message())],
            'title': ['Bar: Hello world'],
            'url': ['http://example.com/baz/bar/issues/{}/'.format(group.id)],
            'url_title': ['Issue Details'],
            'priority': ['0'],
            'user': ['abcdef'],
            'token': ['ghijkl'],
        }
