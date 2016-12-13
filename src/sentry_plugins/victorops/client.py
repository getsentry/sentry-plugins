from __future__ import absolute_import

from requests.exceptions import HTTPError
from sentry.http import build_session

from sentry_plugins.exceptions import ApiError


class VictorOpsClient(object):
    monitoring_tool = 'sentry'
    routing_key = 'everyone'

    def __init__(self, api_key, routing_key=None):
        self.api_key = api_key

        if routing_key:
            self.routing_key = routing_key

    # http://victorops.force.com/knowledgebase/articles/Integration/Alert-Ingestion-API-Documentation/
    def request(self, data):
        endpoint = 'https://alert.victorops.com/integrations/generic/20131114/alert/{}/{}'.format(
            self.api_key,
            self.routing_key,
        )

        session = build_session()
        try:
            resp = session.post(
                url=endpoint,
                json=data,
                allow_redirects=False,
            )
            resp.raise_for_status()
        except HTTPError as e:
            raise ApiError.from_response(e.response)
        return resp.json()

    def trigger_incident(self, message_type, entity_id, timestamp, state_message,
                         entity_display_name=None, monitoring_tool=None, **kwargs):
        kwargs.update({
            'message_type': message_type,
            'entity_id': entity_id,
            'entity_display_name': entity_display_name,
            'timestamp': timestamp,
            'state_message': state_message,
            'monitoring_tool': monitoring_tool or self.monitoring_tool,
        })
        return self.request(kwargs)
