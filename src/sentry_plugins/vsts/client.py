from __future__ import absolute_import

from sentry_plugins.client import AuthApiClient


class VstsClient(AuthApiClient):
    api_version = '3.0'

    def request(self, method, path, data=None, params=None):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json-patch+json'
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
            'https://{}/{}/_apis/wit/workitems/$Bug?api-version={}'.format(
                instance,
                project,
                self.api_version
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
            'https://{}/DefaultCollection/_apis/wit/workitems/{}?api-version={}'.format(
                instance,
                id,
                self.api_version
            ),
            data=data,
        )
