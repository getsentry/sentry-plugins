from __future__ import absolute_import

from sentry_plugins.client import AuthApiClient


class VstsClient(AuthApiClient):
    api_version = '3.0'

    def request(self, method, path, data=None, params=None):
        headers = {
            'Accept': 'application/json; api-version={}'.format(self.api_version),
            'Content-Type': 'application/json-patch+json',
            'X-HTTP-Method-Override': method,
        }
        return self._request(method, path, headers=headers, data=data, params=params)

    def create_work_item(self, instance, project, title, description, link):
        data = [
            {
                'op': 'add',
                'path': '/fields/System.Title',
                'value': title,
            },
            {
                'op': 'add',
                'path': '/fields/System.Description',
                'value': description
            },
            {
                'op': 'add',
                'path': '/relations/-',
                'value': {
                    'rel': 'Hyperlink',
                    'url': link,
                }
            }
        ]

        return self.patch(
            'https://{}/{}/_apis/wit/workitems/$Bug'.format(
                instance,
                project,
            ),
            data=data,
        )

    def update_work_item(self, instance, id, title=None, description=None, link=None,
                         comment=None):
        data = []
        if title:
            data.append({
                'op': 'replace',
                'path': '/fields/System.Title',
                'value': title,
            })
        if description:
            data.append({
                'op': 'replace',
                'path': '/fields/System.Description',
                'value': description
            })
        # TODO(dcramer): this breaks if you unlink + relink on the same issue
        if link:
            data.append({
                'op': 'add',
                'path': '/relations/-',
                'value': {
                    'rel': 'Hyperlink',
                    'url': link,
                }
            })
        if comment:
            data.append({
                'op': 'add',
                'path': '/fields/System.History',
                'value': comment,
            })

        return self.patch(
            'https://{}/DefaultCollection/_apis/wit/workitems/{}'.format(
                instance,
                id,
            ),
            data=data,
        )

    def get_repo(self, instance, name_or_id, project=None):
        return self.get(
            'https://{}/DefaultCollection/{}_apis/git/repositories/{}'.format(
                instance,
                '{}/'.format(project) if project else '',
                name_or_id,
            ),
        )

    def get_commits(self, instance, repo_id, commit, limit=100):
        return self.get(
            'https://{}/DefaultCollection/_apis/git/repositories/{}/commits'.format(
                instance,
                repo_id,
            ),
            params={
                'commit': commit,
                '$top': limit,
            },
        )

    def get_commit_range(self, instance, repo_id, start_sha, end_sha):
        return self.post(
            'https://{}/DefaultCollection/_apis/git/repositories/{}/commitsBatch'.format(
                instance,
                repo_id,
            ),
            data={
                'itemVersion': {
                    'versionType': 'commit',
                    'version': start_sha,
                },
                'compareVersion': {
                    'versionType': 'commit',
                    'version': end_sha
                }
            }
        )

    def get_projects(self, instance):
        # TODO(dcramer): VSTS doesn't provide a way to search, so we're
        # making the assumption that a user has 100 or less projects today.
        return self.get(
            'https://{}/DefaultCollection/_apis/projects'.format(
                instance,
            ),
            params={'stateFilter': 'WellFormed'}
        )
