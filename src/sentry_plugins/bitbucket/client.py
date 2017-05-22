from __future__ import absolute_import

from django.conf import settings
from requests.exceptions import HTTPError
from sentry.http import build_session

from sentry_plugins.exceptions import ApiError

from requests_oauthlib import OAuth1


class BitbucketClient(object):
    API_URL = u'https://api.bitbucket.org/'

    def __init__(self, auth=None):
        self.auth = auth
        # self.token = self.auth.tokens['oauth_token']

    def _request2(self, method, path, data=None, params=None):
        headers = {
            'Authorization': 'token %s' % self.token,
        }

        session = build_session()
        # print(headers)
        print('{}2.0{}'.format(self.API_URL, path))
        try:
            resp = getattr(session, method.lower())(
                url='{}2.0{}'.format(self.API_URL, path),
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

        return self._request(method, path, headers=headers, data=data, params=params)

    def request(self, method, version, path, data=None, params=None):
        # if version=='2.0':
            # return self._request2(method, path, data, params)

        oauth = OAuth1(unicode(settings.BITBUCKET_CONSUMER_KEY),
                       unicode(settings.BITBUCKET_CONSUMER_SECRET),
                       self.auth.tokens['oauth_token'], self.auth.tokens['oauth_token_secret'],
                       signature_type='auth_header')

        session = build_session()
        try:
            resp = getattr(session, method.lower())(
                url='%s%s%s' % (self.API_URL, version, path),
                auth=oauth,
                json=data,
                params=params,
            )
            resp.raise_for_status()
        except HTTPError as e:
            raise ApiError.from_response(e.response)
        return resp.json()

    def get_issue(self, repo, issue_id):
        return self.request(
            'GET',
            '1.0',
            '/repositories/%s/issues/%s' % (repo, issue_id),
        )

    def create_issue(self, repo, data):
        data = {
            'title': data['title'],
            'content': data['description'],
            'kind': data['issue_type'],
            'priority': data['priority']
        }
        return self.request(
            'POST',
            '1.0',
            '/repositories/%s/issues' % (repo,),
            data=data
        )

    def search_issues(self, repo, query):
        return self.request(
            'GET',
            '1.0',
            '/repositories/%s/issues' % (repo,),
            params={'search': query},
        )

    def create_comment(self, repo, issue_id, data):
        return self.request(
            'POST',
            '1.0',
            '/repositories/%s/issues/%s/comments' % (repo, issue_id),
            data=data,
        )

    # copied from github

    def get_repo(self, repo):
        return self.request(
            'GET',
            '2.0',
            '/repositories/{}'.format(repo),
        )

    def create_hook(self, repo, data):
        return self.request(
            'POST',
            '2.0',
            '/repositories/{}/hooks'.format(
                repo,
            ),
            data=data,
        )

    def delete_hook(self, repo, id):
        return self.request(
            'DELETE',
            '2.0',
            '/repositories/{}/hooks/{}'.format(
                repo,
                id,
            ),
        )

    def get_commit_filechanges(self, repo, sha):
        # return api request that fetches last ~30 commits
        # see https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Busername%7D/%7Brepo_slug%7D/commits/%7Brevision%7D
        # using end_sha as parameter
        patch_file =  self.request(
            'GET',
            '2.0',
            '/repositories/{}/patch/{}'.format(
                repo,
                end_sha,
            )
        )


    def get_last_commits(self, repo, end_sha):
        # return api request that fetches last ~30 commits
        # see https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Busername%7D/%7Brepo_slug%7D/commits/%7Brevision%7D
        # using end_sha as parameter
        return self.request(
            'GET',
            '2.0',
            '/repositories/{}/commits/{}'.format(
                repo,
                end_sha,
            )
        )

    def compare_commits(self, repo, start_sha, end_sha):
        # where start sha is oldest and end is most recent
        # see https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Busername%7D/%7Brepo_slug%7D/commits/%7Brevision%7D
        data = self.request(
            'GET',
            '2.0',
            '/repositories/{}/commits/{}'.format(
                repo,
                end_sha
            )
        )
        commits = []
        for commit in data['values']:
            #TODO(maxbittker) fetch extra pages when this is paginated
            if commit['hash'] == start_sha:
                break
            commits.append(commit)
        return commits
