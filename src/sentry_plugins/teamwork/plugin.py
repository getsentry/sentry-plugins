from __future__ import absolute_import

import six

from sentry.exceptions import PluginError
from sentry.plugins import JSONResponse
from sentry.plugins.bases.issue2 import IssuePlugin2
from sentry.utils.http import absolute_uri

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.exceptions import ApiError
from sentry_plugins.utils import get_secret_field_config

from .client import TeamworkClient

ERR_INTERNAL = 'An internal error occurred with the integration and the Sentry team has been notified'


# class TeamworkTaskForm(NewIssueForm):
#     title = forms.CharField(
#         label=_('Title'), max_length=200,
#         widget=forms.TextInput(attrs={'class': 'span9'}))
#     description = forms.CharField(
#         label=_('Description'),
#         widget=forms.Textarea(attrs={'class': 'span9'}))
#     project = forms.ChoiceField(label=_('Project'), choices=())
#     tasklist = forms.ChoiceField(label=_('Task List'), choices=())

#     create_issue_template = 'sentry_teamwork/create_issue.html'

#     def __init__(self, client, data=None, initial=None):
#         super(TeamworkTaskForm, self).__init__(data=data, initial=initial)

#         try:
#             project_list = client.list_projects()
#         except RequestException as e:
#             raise forms.ValidationError(
#                 _('Error contacting Teamwork API: %s') % str(e))

#         self.fields['project'].choices = [
#             (str(i['id']), i['name']) for i in project_list
#         ]
#         self.fields['project'].widget.choices = self.fields['project'].choices

#         if self.data.get('project'):
#             try:
#                 tasklist_list = client.list_tasklists(data['project'])
#             except RequestException as e:
#                 raise forms.ValidationError(
#                     _('Error contacting Teamwork API: %s') % str(e))
#             self.fields['tasklist'].choices = [
#                 (str(i['id']), i['name']) for i in tasklist_list
#             ]
#             self.fields['tasklist'].widget.choices = self.fields['tasklist'].choices


class TeamworkPlugin(CorePluginMixin, IssuePlugin2):
    title = 'Teamwork'
    description = 'Create Teamwork Tasks.'
    slug = 'teamwork'

    conf_title = title
    conf_key = slug

    def _get_group_description(self, request, group, event):
        """
        Return group description in markdown-compatible format.

        This overrides an internal method to IssuePlugin.
        """
        output = [
            absolute_uri(group.get_absolute_url()),
        ]
        body = self._get_group_body(request, group, event)
        if body:
            output.extend([
                '',
                '\n'.join('    ' + line for line in body.splitlines()),
            ])
        return '\n'.join(output)

    def is_configured(self, request, project, **kwargs):
        return all((
            self.get_option(key, project)
            for key in ('url', 'token')
        ))

    def get_config(self, *args, **kwargs):
        return [
            get_secret_field_config(
                name='token',
                label='API Token',
                secret=self.get_option('token', kwargs['project']),
            ),
            {
                'name': 'url',
                'label': 'Teamwork URL',
                'type': 'string',
                'placeholder': 'i.e. http://sentry.teamwork.com',
            },
        ]

    def get_client(self, project):
        return TeamworkClient(
            base_url=self.get_option('url', project),
            token=self.get_option('token', project),
        )

    def get_new_issue_form(self, request, group, event, **kwargs):
        """
        Return a Form for the "Create new issue" page.
        """
        return self.new_issue_form(
            client=self.get_client(group.project),
            data=request.POST or None,
            initial=self.get_initial_form_data(request, group, event),
        )

    def get_issue_url(self, group, issue_id, **kwargs):
        url = self.get_option('url', group.project)
        return '%s/tasks/%s' % (url.rstrip('/'), issue_id)

    def get_new_issue_title(self, **kwargs):
        return 'Create Teamwork Task'

    def raise_error(self, exc):
        if isinstance(exc, ApiError):
            raise PluginError('Error Communicating with Teamwork (HTTP %s): %s' % (
                exc.code,
                exc.json.get('message', 'unknown error') if exc.json else 'unknown error',
            ))
        elif isinstance(exc, PluginError):
            raise
        else:
            self.logger.exception(six.text_type(exc))
            raise PluginError(ERR_INTERNAL)

    def create_issue(self, request, group, form_data, **kwargs):
        client = self.get_client(group.project)
        try:
            task_id = client.create_task(
                content=form_data['title'],
                description=form_data['description'],
                tasklist_id=form_data['tasklist'],
            )
        except Exception as e:
            self.raise_error(e)

        return task_id

    def get_new_issue_fields(self, request, group, event, **kwargs):
        fields = super(TeamworkPlugin, self).get_new_issue_fields(
            request, group, event, **kwargs)
        return [{
            'name': 'project',
            'label': 'Project',
            'type': 'choice',
            'readonly': True
        }, {
            'name': 'tasklist',
            'label': 'Task List',
            'type': 'choice',
            'required': True,
        }] + fields

    # def view(self, request, group, **kwargs):
    #     op = request.GET.get('op')
    #     # TODO(dcramer): add caching
    #     if op == 'getTaskLists':
    #         project_id = request.GET.get('pid')
    #         if not project_id:
    #             return HttpResponse(status=400)

    #         client = self.get_client(group.project)
    #         task_list = client.list_tasklists(project_id)
    #         return JSONResponse([
    #             {'id': i['id'], 'text': i['name']} for i in task_list
    #         ])

    #     return super(TeamworkTaskPlugin, self).view(request, group, **kwargs)
