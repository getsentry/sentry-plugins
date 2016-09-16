from __future__ import absolute_import

import responses

from exam import fixture
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.test.utils import override_settings
from sentry.plugins.bases.issue2 import PluginError
from sentry.testutils import TestCase
from sentry.utils import json

from sentry_plugins.gitlab.plugin import GitLabPlugin


class GitLabPluginTest(TestCase):
    @fixture
    def plugin(self):
        return GitLabPlugin()

    @fixture
    def request(self):
        return RequestFactory()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'gitlab'

    def test_get_issue_label(self):
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert self.plugin.get_issue_label(group, 1) == 'GL-1'

    def test_get_issue_url(self):
        self.plugin.set_option('gitlab_url', 'https://gitlab.com', self.project)
        self.plugin.set_option('gitlab_repo', 'getsentry/sentry', self.project)
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert self.plugin.get_issue_url(group, 1) == 'https://gitlab.com/getsentry/sentry/issues/1'

    def test_is_configured(self):
        assert self.plugin.is_configured(None, self.project) is False
        self.plugin.set_option('gitlab_url', 'https://gitlab.com', self.project)
        assert self.plugin.is_configured(None, self.project) is False
        self.plugin.set_option('gitlab_repo', 'getsentry/sentry', self.project)
        assert self.plugin.is_configured(None, self.project) is False
        self.plugin.set_option('gitlab_token', 'abcdefg', self.project)
        assert self.plugin.is_configured(None, self.project) is True

    @responses.activate
    @override_settings(GITHUB_APP_ID='abc', GITHUB_API_SECRET='123')
    def test_create_issue(self):
        self.plugin.set_option('gitlab_url', 'https://gitlab.com', self.project)
        self.plugin.set_option('gitlab_repo', 'getsentry/sentry', self.project)
        group = self.create_group(message='Hello world', culprit='foo.bar')

        request = self.request.get('/')
        request.user = AnonymousUser()
        form_data = {
            'title': 'Hello',
            'description': 'Fix this.',
        }
        with self.assertRaises(PluginError):
            self.plugin.create_issue(request, group, form_data)

        request.user = self.user
        self.login_as(self.user)

        responses.add(responses.POST, 'https://gitlab.com/api/v3/projects/getsentry%2Fsentry/issues',
            body='{"iid": 1}')
        assert self.plugin.create_issue(request, group, form_data) == 1
        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload == {
            'title': 'Hello',
            'description': 'Fix this.',
            'labels': None,
            'assignee_id': None,
        }
