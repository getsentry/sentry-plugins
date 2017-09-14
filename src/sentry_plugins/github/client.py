from __future__ import absolute_import

import calendar
import datetime
import jwt
import time

from requests.exceptions import HTTPError
from django.conf import settings
from sentry import options
from sentry.http import build_session

from sentry_plugins.exceptions import ApiError


class GitHubClientBase(object):
    url = 'https://api.github.com'

    def _request(self, method, path, headers=None, data=None, params=None):
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

        if resp.status_code == 204:
            return {}

        return resp.json()

    def request(self, method, path, data=None, params=None):
        raise NotImplementedError

    def get_last_commits(self, repo, end_sha):
        # return api request that fetches last ~30 commits
        # see https://developer.github.com/v3/repos/commits/#list-commits-on-a-repository
        # using end_sha as parameter
        return self.request(
            'GET',
            '/repos/{}/commits'.format(
                repo,
            ),
            params={'sha': end_sha},
        )

    def compare_commits(self, repo, start_sha, end_sha):
        # see https://developer.github.com/v3/repos/commits/#compare-two-commits
        # where start sha is oldest and end is most recent
        return self.request('GET', '/repos/{}/compare/{}...{}'.format(
            repo,
            start_sha,
            end_sha,
        ))


class GitHubClient(GitHubClientBase):
    def __init__(self, url=None, token=None):
        if url is not None:
            self.url = url.rstrip('/')
        self.token = token

    def request(self, method, path, data=None, params=None):
        headers = {
            'Authorization': 'token %s' % self.token,
        }

        return self._request(method, path, headers=headers, data=data, params=params)

    def request_no_auth(self, method, path, data=None, params=None):
        if params is None:
            params = {}

        params.update(
            {
                'client_id': settings.GITHUB_APP_ID,
                'client_secret': settings.GITHUB_API_SECRET,
            }
        )

        return self._request(method, path, data=data, params=params)

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
            '/repos/{}/assignees?per_page=100'.format(repo),
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

    def get_installations(self):
        # TODO(jess): remove this whenever it's out of preview
        headers = {
            'Accept': 'application/vnd.github.machine-man-preview+json',
        }

        params = {
            'access_token': self.token,
        }

        return self._request('GET', '/user/installations', headers=headers, params=params)


class GitHubAppsClient(GitHubClientBase):
    url = 'https://api.github.com'

    def __init__(self, integration):
        self.integration = integration
        self.token = None
        self.expires_at = None

    def get_token(self):
        if not self.token or self.expires_at < datetime.datetime.utcnow():
            res = self.create_token()
            self.token = res['token']
            self.expires_at = datetime.datetime.strptime(
                res['expires_at'],
                '%Y-%m-%dT%H:%M:%SZ',
            )

        return self.token

    def get_jwt(self):
        exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        exp = calendar.timegm(exp.timetuple())
        # Generate the JWT
        payload = {
            # issued at time
            'iat': int(time.time()),
            # JWT expiration time (10 minute maximum)
            'exp': exp,
            # Integration's GitHub identifier
            'iss': options.get('github.integration-app-id'),
        }

        return jwt.encode(
            payload, options.get('github.integration-private-key'), algorithm='RS256'
        )

    def request(self, method, path, headers=None, data=None, params=None):
        if headers is None:
            headers = {
                'Authorization': 'token %s' % self.get_token(),
                # TODO(jess): remove this whenever it's out of preview
                'Accept': 'application/vnd.github.machine-man-preview+json',
            }
        return self._request(method, path, headers=headers, data=data, params=params)

    def create_token(self):
        return self.request(
            'POST',
            '/installations/{}/access_tokens'.format(
                self.integration.external_id,
            ),
            headers={
                'Authorization': 'Bearer %s' % self.get_jwt(),
                # TODO(jess): remove this whenever it's out of preview
                'Accept': 'application/vnd.github.machine-man-preview+json',
            },
        )

    def get_repositories(self):
        return self.request(
            'GET',
            '/installation/repositories',
        )
