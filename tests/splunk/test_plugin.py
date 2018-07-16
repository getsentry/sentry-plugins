from __future__ import absolute_import

import responses

from exam import fixture
from sentry.testutils import PluginTestCase
from sentry.utils import json

from sentry_plugins.splunk.plugin import SplunkPlugin


class SplunkPluginTest(PluginTestCase):
    @fixture
    def plugin(self):
        return SplunkPlugin()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'splunk'

    def test_entry_point(self):
        self.assertPluginInstalled('splunk', self.plugin)

    @responses.activate
    def test_simple_notification(self):
        responses.add(responses.POST, 'https://splunk.example.com:8088/services/collector')

        self.plugin.set_option('token', '12345678-1234-1234-1234-1234567890AB', self.project)
        self.plugin.set_option('index', 'main', self.project)
        self.plugin.set_option('instance', 'https://splunk.example.com:8088', self.project)

        group = self.create_group(message='Hello world', culprit='foo.bar')
        event = self.create_event(
            group=group,
            data={
                'sentry.interfaces.Exception': {
                    'type': 'ValueError',
                    'value': 'foo bar',
                },
                'sentry.interfaces.User': {
                    'id': '1',
                    'email': 'foo@example.com',
                },
                'type': 'error',
                'metadata': {
                    'type': 'ValueError',
                    'value': 'foo bar',
                },
            },
            tags={'level': 'warning'},
        )

        with self.options({'system.url-prefix': 'http://example.com'}):
            self.plugin.post_process(event)

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload == {
            'index': 'main',
            'source': 'sentry',
            'time': int(event.datetime.strftime('%s')),
            'event': self.plugin.get_event_payload(event),
        }
        headers = request.headers
        assert headers['Authorization'] == 'Splunk 12345678-1234-1234-1234-1234567890AB'
