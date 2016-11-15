from __future__ import absolute_import

import six

from rest_framework.response import Response

from sentry.exceptions import InvalidIdentity, PluginError, PluginIdentityRequired
from sentry.plugins.bases.issue2 import IssuePlugin2, IssueGroupActionEndpoint
from sentry.utils.http import absolute_uri

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.exceptions import ApiError, ApiUnauthorized
from .client import AsanaClient


ERR_INTERNAL = (
    'An internal error occurred with the integration and '
    'the Sentry team has been notified'
)

ERR_UNAUTHORIZED = (
    'Unauthorized: either your access token was invalid or '
    'you do not have access'
)

ERR_AUTH_NOT_CONFIGURED = (
    'You still need to associate an Asana identity with this account.'
)


class AsanaPlugin(CorePluginMixin, IssuePlugin2):
    description = 'Integrate Asana issues by linking a repository to a project.'
    slug = 'asana'
    title = 'Asana'
    conf_title = title
    conf_key = 'asana'
    auth_provider = 'asana'

    def get_group_urls(self):
        return super(AsanaPlugin, self).get_group_urls() + [
            (r'^autocomplete', IssueGroupActionEndpoint.as_view(
                view_method_name='view_autocomplete',
                plugin=self,
            )),
        ]

    def is_configured(self, request, project, **kwargs):
        return bool(self.get_option('workspace', project))

    def has_workspace_access(self, workspace, choices):
        for c, _ in choices:
            if workspace == c:
                return True
        return False

    def get_workspace_choices(self, workspaces):
        return [(w['id'], w['name']) for w in workspaces['data']]

    def get_new_issue_fields(self, request, group, event, **kwargs):
        fields = super(AsanaPlugin, self).get_new_issue_fields(request, group, event, **kwargs)
        client = self.get_client(request.user)
        workspaces = client.get_workspaces()
        workspace_choices = self.get_workspace_choices(workspaces)
        workspace = self.get_option('workspace', group.project)
        if workspace and not self.has_workspace_access(workspace, workspace_choices):
            workspace_choices.append((workspace, workspace))

        # use labels that are more applicable to asana
        for field in fields:
            if field['name'] == 'title':
                field['label'] = 'Name'
            if field['name'] == 'description':
                field['label'] = 'Notes'
                field['required'] = False

        return [{
            'name': 'workspace',
            'label': 'Asana Workspace',
            'default': workspace,
            'type': 'select',
            'choices': workspace_choices,
            'readonly': True
        }] + fields + [{
            'name': 'project',
            'label': 'Project',
            'type': 'select',
            'has_autocomplete': True,
            'required': False,
            'placeholder': 'Start typing to search for a project'
        }, {
            'name': 'assignee',
            'label': 'Assignee',
            'type': 'select',
            'has_autocomplete': True,
            'required': False,
            'placeholder': 'Start typing to search for a user'
        }]

    def get_link_existing_issue_fields(self, request, group, event, **kwargs):
        return [{
            'name': 'issue_id',
            'label': 'Task',
            'default': '',
            'type': 'select',
            'has_autocomplete': True
        }, {
            'name': 'comment',
            'label': 'Comment',
            'default': absolute_uri(group.get_absolute_url()),
            'type': 'textarea',
            'help': ('Leave blank if you don\'t want to '
                     'add a comment to the Asana issue.'),
            'required': False
        }]

    def get_client(self, user):
        auth = self.get_auth_for_user(user=user)
        if auth is None:
            raise PluginIdentityRequired(ERR_AUTH_NOT_CONFIGURED)
        return AsanaClient(auth=auth)

    def message_from_error(self, exc):
        if isinstance(exc, ApiUnauthorized):
            return ERR_UNAUTHORIZED
        elif isinstance(exc, ApiError):
            message = 'unknown error'
            errors = exc.json and exc.json.get('errors')
            if errors:
                message = ' '.join([e['message'] for e in errors])
            return ('Error Communicating with Asana (HTTP %s): %s' % (
                exc.code,
                message
            ))
        else:
            return ERR_INTERNAL

    def raise_error(self, exc):
        if isinstance(exc, ApiUnauthorized):
            raise InvalidIdentity(self.message_from_error(exc))
        elif isinstance(exc, ApiError):
            raise PluginError(self.message_from_error(exc))
        elif isinstance(exc, PluginError):
            raise
        else:
            self.logger.exception(six.text_type(exc))
            raise PluginError(self.message_from_error(exc))

    def create_issue(self, request, group, form_data, **kwargs):
        client = self.get_client(request.user)

        try:
            response = client.create_issue(
                workspace=self.get_option('workspace', group.project),
                data=form_data
            )
        except Exception as e:
            self.raise_error(e)

        return response['data']['id']

    def link_issue(self, request, group, form_data, **kwargs):
        client = self.get_client(request.user)
        try:
            issue = client.get_issue(
                issue_id=form_data['issue_id'],
            )['data']
        except Exception as e:
            self.raise_error(e)

        comment = form_data.get('comment')
        if comment:
            try:
                client.create_comment(issue['id'], {'text': comment})
            except Exception as e:
                self.raise_error(e)

        return {
            'title': issue['name']
        }

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'Asana Issue'

    def get_issue_url(self, group, issue_id, **kwargs):
        return 'https://app.asana.com/0/0/%s' % issue_id

    def validate_config(self, project, config, actor):
        """
        ```
        if config['foo'] and not config['bar']:
            raise PluginError('You cannot configure foo with bar')
        return config
        ```
        """
        try:
            config['workspace'] = int(config['workspace'])
        except ValueError as exc:
            self.logger.exception(six.text_type(exc))
            raise PluginError('Invalid workspace value')
        return config

    def get_config(self, *args, **kwargs):
        user = kwargs['user']
        try:
            client = self.get_client(user)
        except PluginIdentityRequired as e:
            self.raise_error(e)
        workspaces = client.get_workspaces()
        workspace_choices = self.get_workspace_choices(workspaces)
        workspace = self.get_option('workspace', kwargs['project'])
        # check to make sure the current user has access to the workspace
        helptext = None
        if workspace and not self.has_workspace_access(workspace, workspace_choices):
            workspace_choices.append((workspace, workspace))
            helptext = ('This plugin has been configured for an Asana workspace '
                        'that either you don\'t have access to or doesn\'t '
                        'exist. You can edit the configuration, but you will not '
                        'be able to change it back to the current configuration '
                        'unless a teammate grants you access to the workspace in Asana.')
        return [{
            'name': 'workspace',
            'label': 'Workspace',
            'type': 'select',
            'choices': workspace_choices,
            'default': workspace or workspaces['data'][0]['id'],
            'help': helptext
        }]

    def view_autocomplete(self, request, group, **kwargs):
        field = request.GET.get('autocomplete_field')
        query = request.GET.get('autocomplete_query')

        client = self.get_client(request.user)
        workspace = self.get_option('workspace', group.project)
        results = []
        field_name = field
        if field == 'issue_id':
            field_name = 'task'
        elif field == 'assignee':
            field_name = 'user'
        try:
            response = client.search(workspace, field_name, query.encode('utf-8'))
        except Exception as e:
            return Response({
                'error_type': 'validation',
                'errors': [{'__all__': self.message_from_error(e)}]
            }, status=400)
        else:
            results = [{
                'text': '(#%s) %s' % (i['id'], i['name']),
                'id': i['id']
            } for i in response.get('data', [])]

        return Response({field: results})
