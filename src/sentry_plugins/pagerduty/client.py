from __future__ import absolute_import

from requests.exceptions import HTTPError
from sentry.http import build_session
from sentry.utils.http import absolute_uri

from sentry_plugins.exceptions import ApiError

# https://v2.developer.pagerduty.com/docs/events-api
INTEGRATION_API_URL = \
    'https://events.pagerduty.com/generic/2010-04-15/create_event.json'


class PagerDutyClient(object):
    client = 'sentry'

    def __init__(self, service_key=None):
        self.service_key = service_key

    def request(self, data):
        payload = {
            'service_key': self.service_key,
        }
        payload.update(data)

        session = build_session()
        try:
            resp = session.post(
                url=INTEGRATION_API_URL,
                json=payload,
                allow_redirects=False,
            )
            resp.raise_for_status()
        except HTTPError as e:
            raise ApiError.from_response(e.response)
        return resp.json()

    def trigger_incident(self, description, event_type, details, incident_key,
                         client=None, client_url=None, contexts=None):
        return self.request({
            'event_type': event_type,
            'description': description,
            'details': details,
            'incident_key': incident_key,
            'client': client or self.client,
            'client_url': client_url or absolute_uri(),
            'contexts': contexts,
        })
