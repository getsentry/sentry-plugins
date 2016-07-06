from __future__ import absolute_import

import responses
from exam import fixture
from django.contrib.auth.models import AnonymousUser
from django.forms import ValidationError
from django.test import RequestFactory
from django.test.utils import override_settings
from sentry.testutils import TestCase
from sentry.utils import json
from social_auth.models import UserSocialAuth

from sentry_github.plugin import GitHubPlugin


class GitHubPluginTest(TestCase):
    @fixture
    def plugin(self):
        return GitHubPlugin()

    @fixture
    def request(self):
        return RequestFactory()

    def test_get_issue_label(self):
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert self.plugin.get_issue_label(group, 1) == 'GH-1'

    def test_get_issue_url(self):
        self.plugin.set_option('repo', 'getsentry/sentry', self.project)
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert self.plugin.get_issue_url(group, 1) == 'https://github.com/getsentry/sentry/issues/1'

    def test_is_configured(self):
        assert self.plugin.is_configured(None, self.project) is False
        self.plugin.set_option('repo', 'getsentry/sentry', self.project)
        assert self.plugin.is_configured(None, self.project) is True

    @responses.activate
    @override_settings(GITHUB_APP_ID='abc', GITHUB_API_SECRET='123')
    def test_create_issue(self):
        self.plugin.set_option('repo', 'getsentry/sentry', self.project)
        group = self.create_group(message='Hello world', culprit='foo.bar')

        request = self.request.get('/')
        request.user = AnonymousUser()
        form_data = {
            'title': 'Hello',
            'description': 'Fix this.',
        }
        with self.assertRaises(ValidationError):
            self.plugin.create_issue(request, group, form_data)

        request.user = self.user
        self.login_as(self.user)
        UserSocialAuth.objects.create(user=self.user, provider=self.plugin.auth_provider, extra_data={'access_token': 'foo'})

        responses.add(responses.POST, 'https://api.github.com/repos/getsentry/sentry/issues',
            body='{"number": 1}')
        assert self.plugin.create_issue(request, group, form_data) == 1
        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload == {
            'title': 'Hello',
            'body': 'Fix this.',
            'assignee': None
        }
