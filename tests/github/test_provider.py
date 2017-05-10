from __future__ import absolute_import

from exam import fixture
from sentry.models import Repository
from sentry.testutils import PluginTestCase
from sentry.utils import json

from sentry_plugins.github.plugin import GitHubRepositoryProvider
from sentry_plugins.github.testutils import COMPARE_COMMITS_EXAMPLE, GET_LAST_COMMITS_EXAMPLE


class GitHubPluginTest(PluginTestCase):
    @fixture
    def provider(self):
        return GitHubRepositoryProvider('github')

    def test_compare_commits(self):
        repo = Repository.objects.create(
            provider='github',
            name='example',
            organization_id=1,
        )

        res = self.provider._format_commits(repo, json.loads(COMPARE_COMMITS_EXAMPLE)['commits'])

        assert res == [{
            'author_email': 'support@github.com',
            'author_name': 'Monalisa Octocat',
            'message': 'Fix all the bugs',
            'id': '6dcb09b5b57875f334f61aebed695e2e4193db5e',
            'repository': 'example'
        }]

    def test_get_last_commits(self):
        repo = Repository.objects.create(
            provider='github',
            name='example',
            organization_id=1,
        )

        res = self.provider._format_commits(repo, json.loads(GET_LAST_COMMITS_EXAMPLE)[:10])

        assert res == [{
            'author_email': 'support@github.com',
            'author_name': 'Monalisa Octocat',
            'message': 'Fix all the bugs',
            'id': '6dcb09b5b57875f334f61aebed695e2e4193db5e',
            'repository': 'example'
        }]
