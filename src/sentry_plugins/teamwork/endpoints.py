from __future__ import absolute_import

from rest_framework.response import Response
from sentry.plugins.bases.issue2 import IssueGroupActionEndpoint


class TeamworkTasksEndpoint(IssueGroupActionEndpoint):
    def get(self, request, group, **kwargs):
        project_id = request.GET.get('pid')
        if not project_id:
            return Response(status=400)

        client = self.plugin.get_client(group.project)
        task_list = client.list_tasklists(project_id)
        return Response([
            {'id': i['id'], 'text': i['name']} for i in task_list
        ])
