from __future__ import absolute_import

import responses

from exam import fixture
from sentry.models import Rule
from sentry.plugins import Notification
from sentry.testutils import PluginTestCase
from sentry.utils import json

from sentry_plugins.victorops.plugin import VictorOpsPlugin

SUCCESS = """{
  "result":"success",
  "entity_id":"86dc4115-72d3-4219-9d8e-44939c1c409d"
}"""


class VictorOpsPluginTest(PluginTestCase):
    @fixture
    def plugin(self):
        return VictorOpsPlugin()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'victorops'

    def test_entry_point(self):
        self.assertAppInstalled('victorops', 'sentry_plugins.victorops')
        self.assertPluginInstalled('victorops', self.plugin)

    def test_is_configured(self):
        assert self.plugin.is_configured(self.project) is False
        self.plugin.set_option('api_key', 'abcdef', self.project)
        assert self.plugin.is_configured(self.project) is True

    @responses.activate
    def test_simple_notification(self):
        responses.add('POST', 'https://alert.victorops.com/integrations/generic/20131114/alert/secret-api-key/everyone',
                      body=SUCCESS)
        self.plugin.set_option('api_key', 'secret-api-key', self.project)
        self.plugin.set_option('routing_key', 'everyone', self.project)

        group = self.create_group(message='Hello world', culprit='foo.bar')
        event = self.create_event(group=group, message='Hello world', tags={'level': 'warning'})

        rule = Rule.objects.create(project=self.project, label='my rule')

        notification = Notification(event=event, rule=rule)

        with self.options({'system.url-prefix': 'http://example.com'}):
            self.plugin.notify(notification)

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert {
            'message_type': 'WARNING',
            'entity_id': group.id,
            'entity_display_name': 'Hello world',
            'monitoring_tool': 'sentry',
            'state_message': 'Stacktrace\n-----------\n\nStacktrace (most recent call last):\n\n  File "raven/base.py", line 29, in build_msg\n    string_max_length=self.string_max_length)\n\nMessage\n-----------\n\nHello world',
            'timestamp': int(event.datetime.strftime('%s')),
        } == payload
