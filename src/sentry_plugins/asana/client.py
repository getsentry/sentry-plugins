from __future__ import absolute_import

from requests.exceptions import HTTPError
from sentry.http import build_session

from sentry_plugins.exceptions import ApiError, ApiUnauthorized


class AsanaClient(object):
    API_URL = u'https://app.asana.com/api/1.0'

    def __init__(self, auth):
        self.auth = auth

    def _request(self, token, method, path, data=None, params=None):
        headers = {
            'Authorization': 'Bearer %s' % token,
        }

        session = build_session()
        try:
            resp = getattr(session, method.lower())(
                url='%s%s' % (self.API_URL, path),
                headers=headers,
                json=data,
                params=params,
                allow_redirects=False,
            )
            resp.raise_for_status()
        except HTTPError as e:
            raise ApiError.from_response(e.response)
        return resp.json()

    def request(self, method, path, data=None, params=None):
        token = self.auth.tokens['access_token']
        try:
            return self._request(token, method, path, data=data, params=params)
        except ApiUnauthorized:
            # refresh token
            self.auth.refresh_token()
            token = self.auth.tokens['access_token']
            return self._request(token, method, path, data=data, params=params)

    def get_workspaces(self):
        return self.request('GET', '/workspaces')

    def get_issue(self, issue_id):
        return self.request(
            'GET',
            '/tasks/%s' % issue_id,
        )

    def create_issue(self, workspace, data):
        asana_data = {
            'name': data['title'],
            'notes': data['description'],
            'workspace': workspace
        }
        if data.get('project'):
            asana_data['projects'] = data['project']

        if data.get('assignee'):
            asana_data['assignee'] = data['assignee']

        return self.request(
            'POST',
            '/tasks',
            data={'data': asana_data}
        )

    def create_comment(self, issue_id, data):
        return self.request(
            'POST',
            '/tasks/%s/stories/' % issue_id,
            data={'data': data},
        )

    def search(self, workspace, object_type, query):
        return self.request(
            'GET',
            '/workspaces/%s/typeahead' % workspace,
            params={'type': object_type, 'query': query}
        )
