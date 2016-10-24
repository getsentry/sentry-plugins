from __future__ import absolute_import

from django.conf import settings
from requests.exceptions import HTTPError
from sentry.http import build_session

from sentry_plugins.exceptions import ApiError

from requests_oauthlib import OAuth1


class BitbucketClient(object):
    API_URL = u'https://api.bitbucket.org/1.0'

    def __init__(self, auth):
        self.auth = auth

    def request(self, method, path, data=None, params=None):
        oauth = OAuth1(unicode(settings.BITBUCKET_CONSUMER_KEY),
                       unicode(settings.BITBUCKET_CONSUMER_SECRET),
                       self.auth.tokens['oauth_token'], self.auth.tokens['oauth_token_secret'],
                       signature_type='auth_header')

        session = build_session()
        try:
            resp = getattr(session, method.lower())(
                url='%s%s' % (self.API_URL, path),
                auth=oauth,
                data=data,
                params=params,
            )
            resp.raise_for_status()
        except HTTPError as e:
            raise ApiError.from_response(e.response)
        return resp.json()

    def get_issue(self, repo, issue_id):
        return self.request(
            'GET',
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
            '/repositories/%s/issues' % (repo,),
            data=data
        )

    def search_issues(self, repo, query):
        return self.request(
            'GET',
            '/repositories/%s/issues' % (repo,),
            params={'search': query},
        )

    def create_comment(self, repo, issue_id, data):
        return self.request(
            'POST',
            '/repositories/%s/issues/%s/comments' % (repo, issue_id),
            data=data,
        )
