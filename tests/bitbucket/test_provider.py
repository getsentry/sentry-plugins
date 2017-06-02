from __future__ import absolute_import

from exam import fixture
from sentry.models import Repository
from sentry.testutils import PluginTestCase
from sentry.utils import json

from sentry_plugins.bitbucket.plugin import BitbucketRepositoryProvider
from sentry_plugins.bitbucket.testutils import COMPARE_COMMITS_EXAMPLE


class BitbucketPluginTest(PluginTestCase):
    @fixture
    def provider(self):
        return BitbucketRepositoryProvider('bitbucket')

    def test_compare_commits(self):
        repo = Repository.objects.create(
            provider='bitbucket',
            name='maxbittker/newsdiffs',
            organization_id=1,
        )

        res = self.provider._format_commits(repo, json.loads(COMPARE_COMMITS_EXAMPLE)['values'])

        assert res == [{
            'author_email': 'max@getsentry.com',
            'author_name': 'Max Bittker',
            'message': 'README.md edited online with Bitbucket',
            'id': 'e18e4e72de0d824edfbe0d73efe34cbd0d01d301',
            'repository': 'maxbittker/newsdiffs',
            'patch_set': None
        }]
