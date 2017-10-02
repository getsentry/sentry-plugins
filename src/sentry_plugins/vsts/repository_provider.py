from __future__ import absolute_import

import six

from sentry.plugins import providers
from six.moves.urllib.parse import urlparse

from .mixins import VisualStudioMixin


class VisualStudioRepositoryProvider(VisualStudioMixin, providers.RepositoryProvider):
    name = 'Visual Studio'
    auth_provider = 'visualstudio'

    def get_config(self):
        return [
            {
                'name': 'url',
                'label': 'Repository URL',
                'type': 'text',
                'placeholder': 'e.g. https://example.visualstudio.com/_git/MyFirstProject',
                'required': True,
            },
            {
                'name': 'project',
                'label': 'Project Name',
                'type': 'text',
                'placeholder': 'e.g. MyFirstProject',
                'help': 'Optional project name if it does not match the repository name',
                'required': False,
            }
        ]

    def validate_config(self, organization, config, actor=None):
        if config.get('url'):
            client = self.get_client(actor)
            # parse out the repo name and the instance
            parts = urlparse(config['url'])
            instance = parts.netloc
            name = parts.path.rsplit('_git/', 1)[-1]
            project = config.get('project') or name

            try:
                repo = client.get_repo(instance, name, project)
            except Exception as e:
                self.raise_error(e, identity=client.auth)
            config.update({
                'instance': instance,
                'project': project,
                'name': repo['name'],
                'external_id': six.text_type(repo['id']),
                'url': repo['_links']['web']['href'],
            })
        return config

    def create_repository(self, organization, data, actor=None):
        if actor is None:
            raise NotImplementedError('Cannot create a repository anonymously')

        return {
            'name': data['name'],
            'external_id': data['external_id'],
            'url': data['url'],
            'config': {
                'instance': data['instance'],
                'project': data['project'],
                'name': data['name'],
            }
        }

    def delete_repository(self, repo, actor=None):
        pass

    def compare_commits(self, repo, start_sha, end_sha, actor=None):
        if actor is None:
            raise NotImplementedError('Cannot fetch commits anonymously')

        client = self.get_client(actor)
        instance = repo.config['instance']
        if start_sha is None:
            try:
                res = client.get_commits(instance, repo.external_id, commit=end_sha, limit=10)
            except Exception as e:
                self.raise_error(e, identity=client.auth)
            else:
                return self._format_commits(repo, res['value'])
        else:
            try:
                res = client.get_commit_range(instance, repo.external_id, start_sha, end_sha)
            except Exception as e:
                self.raise_error(e, identity=client.auth)
            else:
                return self._format_commits(repo, res)

    def _format_commits(self, repo, commit_list):
        return [
            {
                'id': c['commitId'],
                'repository': repo.name,
                'author_email': c['author']['email'],
                'author_name': c['author']['name'],
                'message': c['comment'],
            } for c in commit_list
        ]
