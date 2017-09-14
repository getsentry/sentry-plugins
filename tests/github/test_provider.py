from __future__ import absolute_import

from mock import patch

from exam import fixture
from social_auth.models import UserSocialAuth
from sentry.models import Integration, OrganizationIntegration, Repository
from sentry.testutils import PluginTestCase
from sentry.utils import json

from sentry_plugins.github.client import GitHubClient, GitHubAppsClient
from sentry_plugins.github.plugin import GitHubAppsRepositoryProvider, GitHubRepositoryProvider
from sentry_plugins.github.testutils import (
    COMPARE_COMMITS_EXAMPLE, GET_LAST_COMMITS_EXAMPLE, INTSTALLATION_REPOSITORIES_API_RESPONSE,
    LIST_INSTALLATION_API_RESPONSE
)


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

        assert res == [
            {
                'author_email': 'support@github.com',
                'author_name': 'Monalisa Octocat',
                'message': 'Fix all the bugs',
                'id': '6dcb09b5b57875f334f61aebed695e2e4193db5e',
                'repository': 'example'
            }
        ]

    def test_get_last_commits(self):
        repo = Repository.objects.create(
            provider='github',
            name='example',
            organization_id=1,
        )

        res = self.provider._format_commits(repo, json.loads(GET_LAST_COMMITS_EXAMPLE)[:10])

        assert res == [
            {
                'author_email': 'support@github.com',
                'author_name': 'Monalisa Octocat',
                'message': 'Fix all the bugs',
                'id': '6dcb09b5b57875f334f61aebed695e2e4193db5e',
                'repository': 'example'
            }
        ]


class GitHubAppsProviderTest(PluginTestCase):
    @fixture
    def provider(self):
        return GitHubAppsRepositoryProvider('github_apps')

    @patch.object(
        GitHubAppsClient,
        'get_repositories',
        return_value=json.loads(INTSTALLATION_REPOSITORIES_API_RESPONSE)
    )
    @patch.object(
        GitHubClient, 'get_installations', return_value=json.loads(LIST_INSTALLATION_API_RESPONSE)
    )
    def test_link_auth(self, *args):
        user = self.create_user()
        organization = self.create_organization()
        UserSocialAuth.objects.create(
            user=user,
            provider='github_apps',
            extra_data={'access_token': 'abcdefg'},
        )

        integration = Integration.objects.create(
            provider='github_apps',
            external_id='1',
        )

        self.provider.link_auth(user, organization, {'integration_id': integration.id})

        assert OrganizationIntegration.objects.filter(
            organization=organization, integration=integration
        ).exists()

    def test_delete_repository(self):
        user = self.create_user()
        organization = self.create_organization()
        integration = Integration.objects.create(
            provider='github_apps',
            external_id='1',
        )
        repo = Repository.objects.create(
            name='example-repo',
            provider='github_apps',
            organization_id=organization.id,
            integration_id=integration.id,
        )

        # just check that it doesn't throw / try to delete a webhook
        assert self.provider.delete_repository(repo=repo, actor=user) is None

    @patch.object(
        GitHubAppsClient,
        'get_last_commits',
        return_value=[]
    )
    def test_compare_commits_no_start(self, mock_get_last_commits):
        organization = self.create_organization()
        integration = Integration.objects.create(
            provider='github_apps',
            external_id='1',
        )
        repo = Repository.objects.create(
            name='example-repo',
            provider='github_apps',
            organization_id=organization.id,
            integration_id=integration.id,
            config={'name': 'example-repo'},
        )

        self.provider.compare_commits(repo, None, 'a' * 40)

        assert mock_get_last_commits.called

    @patch.object(
        GitHubAppsClient,
        'compare_commits',
        return_value={'commits': []}
    )
    def test_compare_commits(self, mock_compare_commits):
        organization = self.create_organization()
        integration = Integration.objects.create(
            provider='github_apps',
            external_id='1',
        )
        repo = Repository.objects.create(
            name='example-repo',
            provider='github_apps',
            organization_id=organization.id,
            integration_id=integration.id,
            config={'name': 'example-repo'},
        )

        self.provider.compare_commits(repo, 'b' * 40, 'a' * 40)

        assert mock_compare_commits.called
