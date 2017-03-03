from __future__ import absolute_import

import responses

from exam import fixture
from sentry.testutils import PluginTestCase
from sentry.utils import json

from sentry_plugins.sessionstack.plugin import SessionStackPlugin

import pytest


EXPECTED_SESSION_URL = (
    'https://app.sessionstack.com/player/#/sessions/588778a6c5762c1d566653ff'
    '?access_token=example-access-token'
)

ACCESS_TOKENS_URL = (
    'https://api.sessionstack.com/v1/websites/0/sessions/'
    '588778a6c5762c1d566653ff/access_tokens'
)


@pytest.mark.xfail
class SessionStackPluginTest(PluginTestCase):
    @fixture
    def plugin(self):
        return SessionStackPlugin()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'sessionstack'

    def test_entry_point(self):
        self.assertAppInstalled('sessionstack', 'sentry_plugins.sessionstack')
        self.assertPluginInstalled('sessionstack', self.plugin)

    @responses.activate
    def test_config_validation(self):
        responses.add(responses.GET, 'https://api.sessionstack.com/v1/websites/0')

        config = {
            'account_email': 'user@example.com',
            'api_token': 'example-api-token',
            'website_id': 0
        }

        self.plugin.validate_config(self.project, config)

    @responses.activate
    def test_event_preprocessing(self):
        responses.add(
            responses.GET,
            ACCESS_TOKENS_URL,
            body=json.dumps({
                'data': [
                    {
                        'name': 'Sentry',
                        'access_token': 'example-access-token'
                    }
                ]
            })
        )

        self.plugin.set_option('account_email', 'user@example.com', self.project)
        self.plugin.set_option('api_token', 'example-api-token', self.project)
        self.plugin.set_option('website_id', 0, self.project)

        event_preprocessors = self.plugin.get_event_preprocessors(None)
        add_sessionstack_context = event_preprocessors[0]

        event = {
            'project': self.project.id,
            'extra': {
                'sessionstack': {
                    'session_id': '588778a6c5762c1d566653ff'
                }
            }
        }

        processed_event = add_sessionstack_context(event)

        event_contexts = processed_event.get('contexts')
        sessionstack_context = event_contexts.get('sessionstack')
        session_url = sessionstack_context.get('session_url')

        assert session_url == EXPECTED_SESSION_URL
