from __future__ import absolute_import

from requests.exceptions import HTTPError
from sentry.http import build_session

from sentry_plugins.exceptions import ApiError


class PushoverClient(object):
    base_url = 'https://api.pushover.net/1'

    def __init__(self, userkey=None, apikey=None):
        self.userkey = userkey
        self.apikey = apikey

    def request(self, method, path, data):
        # see https://pushover.net/api
        # We can no longer send JSON because pushover disabled incoming
        # JSON data: http://updates.pushover.net/post/39822700181/
        payload = {
            'user': self.userkey,
            'token': self.apikey,
        }
        payload.update(data)

        session = build_session()
        try:
            resp = getattr(session, method.lower())(
                url='{}{}'.format(self.base_url, path),
                data=payload,
                allow_redirects=False,
            )
            resp.raise_for_status()
        except HTTPError as e:
            raise ApiError.from_response(e.response)
        return resp.json()

    def send_message(self, data):
        return self.request('POST', '/messages.json', data)
