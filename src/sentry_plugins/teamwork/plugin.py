from __future__ import absolute_import

import six

import sentry_plugins

from django import forms
from django.utils.translation import ugettext_lazy as _
from requests.exceptions import RequestException
from sentry.plugins import JSONResponse
from sentry.plugins.bases.issue2 import IssuePlugin2
from sentry.utils.http import absolute_uri

from .client import TeamworkClient


class TeamworkTaskForm(NewIssueForm):
    title = forms.CharField(
        label=_('Title'), max_length=200,
        widget=forms.TextInput(attrs={'class': 'span9'}))
    description = forms.CharField(
        label=_('Description'),
        widget=forms.Textarea(attrs={'class': 'span9'}))
    project = forms.ChoiceField(label=_('Project'), choices=())
    tasklist = forms.ChoiceField(label=_('Task List'), choices=())

    create_issue_template = 'sentry_teamwork/create_issue.html'

    def __init__(self, client, data=None, initial=None):
        super(TeamworkTaskForm, self).__init__(data=data, initial=initial)

        try:
            project_list = client.list_projects()
        except RequestException as e:
            raise forms.ValidationError(
                _('Error contacting Teamwork API: %s') % str(e))

        self.fields['project'].choices = [
            (str(i['id']), i['name']) for i in project_list
        ]
        self.fields['project'].widget.choices = self.fields['project'].choices

        if self.data.get('project'):
            try:
                tasklist_list = client.list_tasklists(data['project'])
            except RequestException as e:
                raise forms.ValidationError(
                    _('Error contacting Teamwork API: %s') % str(e))
            self.fields['tasklist'].choices = [
                (str(i['id']), i['name']) for i in tasklist_list
            ]
            self.fields['tasklist'].widget.choices = self.fields['tasklist'].choices


class TeamworkPlugin(IssuePlugin2):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry/sentry-plugins'
    version = sentry_plugins.VERSION
    description = 'Integrate Teamwork tasks by linking a repository to a project.'
    resource_links = [
        ('Bug Tracker', 'https://github.com/getsentry/sentry-plugins/issues'),
        ('Source', 'https://github.com/getsentry/sentry-plugins'),
    ]
    title = _('Teamwork')
    description = _('Create Teamwork Tasks.')
    slug = 'teamwork'

    conf_title = title
    conf_key = slug

    version = sentry_teamwork.VERSION

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


    def get_group_urls(self):
        return super(TeamworkPlugin, self).get_group_urls() + (
            r'^tasks/$', TeamworkTasksEndpoint.as_view(plugin=self),
        )

    def is_configured(self, request, project, **kwargs):
        return all((
            self.get_option(key, project)
            for key in ('url', 'token')
        ))

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

    def create_issue(self, request, group, form_data, **kwargs):
        client = self.get_client(group.project)
        try:
            task_id = client.create_task(
                content=form_data['title'],
                description=form_data['description'],
                tasklist_id=form_data['tasklist'],
            )
        except RequestException as e:
            raise PluginError('Error creating Teamwork task: %s' % six.text_type(e))

        return task_id

    def get_configure_plugin_fields(self, request, project, **kwargs):
        return [{
            'name': 'url',
            'label': 'Teamwork URL',
            'type': 'url',
            'placeholder': 'e.g. http://sentry.teamwork.com',
            'required': True,
            'help': 'Enter the URL for your Teamwork server.'
        }, {
            'name': 'token',
            'label': 'API Token',
            'type': 'secret',
            'required': True,
            'help': 'Enter your Teamwork API token.'
        }]
