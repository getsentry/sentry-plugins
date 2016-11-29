from __future__ import absolute_import

from requests.exceptions import HTTPError
from sentry.http import build_session

from sentry_plugins.exceptions import ApiError


class GitHubClient(object):
    url = 'https://api.github.com'

    def __init__(self, url=None, token=None):
        if url is not None:
            self.url = url.rstrip('/')
        self.token = token

    def request(self, method, path, data=None, params=None):
        headers = {
            'Authorization': 'token %s' % self.token,
        }

        session = build_session()
        try:
            resp = getattr(session, method.lower())(
                url='{}{}'.format(self.url, path),
                headers=headers,
                json=data,
                params=params,
                allow_redirects=True,
            )
            resp.raise_for_status()
        except HTTPError as e:
            raise ApiError.from_response(e.response)
        return resp.json()

    def get_repo(self, repo):
        return self.request(
            'GET',
            '/repos/{}'.format(repo),
        )

    def get_issue(self, repo, issue_id):
        return self.request(
            'GET',
            '/repos/{}/issues/{}'.format(repo, issue_id),
        )

    def create_issue(self, repo, data):
        return self.request(
            'POST',
            '/repos/{}/issues'.format(repo),
            data=data,
        )

    def create_comment(self, repo, issue_id, data):
        return self.request(
            'POST',
            '/repos/{}/issues/{}/comments'.format(
                repo,
                issue_id,
            ),
            data=data,
        )

    def list_assignees(self, repo):
        return self.request(
            'GET',
            '/repos/{}/assignees'.format(repo),
        )

    def search_issues(self, query):
        return self.request(
            'GET',
            '/search/issues',
            params={'q': query},
        )

    def create_hook(self, repo, data):
        return self.request(
            'POST',
            '/repos/{}/hooks'.format(
                repo,
            ),
            data=data,
        )

    def delete_hook(self, repo, id):
        return self.request(
            'DELETE',
            '/repos/{}/hooks/{}'.format(
                repo,
                id,
            ),
        )
