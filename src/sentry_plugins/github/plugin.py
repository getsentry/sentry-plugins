from __future__ import absolute_import

import six

from rest_framework.response import Response

from sentry.plugins.bases.issue2 import IssuePlugin2, IssueGroupActionEndpoint, PluginError
from sentry.utils.http import absolute_uri

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.exceptions import ApiError, ApiUnauthorized

from .client import GitHubClient

ERR_INTERNAL = (
    'An internal error occurred with the integration and the Sentry team has'
    ' been notified'
)

ERR_UNAUTHORIZED = (
    'Unauthorized: either your access token was invalid or you do not have'
    ' access'
)

ERR_404 = (
    'GitHub returned a 404 Not Found error. If this repository exists, ensure'
    ' you have access to it and that Sentry is being allowed to read data from'
    ' this organization (Account Settings > Authorized Applications > Sentry).'
)


class GitHubPlugin(CorePluginMixin, IssuePlugin2):
    description = 'Integrate GitHub issues by linking a repository to a project.'
    slug = 'github'
    title = 'GitHub'
    conf_title = title
    conf_key = 'github'
    auth_provider = 'github'

    def get_group_urls(self):
        return super(GitHubPlugin, self).get_group_urls() + [
            (r'^autocomplete', IssueGroupActionEndpoint.as_view(
                view_method_name='view_autocomplete',
                plugin=self,
            )),
        ]

    def is_configured(self, request, project, **kwargs):
        return bool(self.get_option('repo', project))

    def get_new_issue_fields(self, request, group, event, **kwargs):
        fields = super(GitHubPlugin, self).get_new_issue_fields(request, group, event, **kwargs)
        return [{
            'name': 'repo',
            'label': 'GitHub Repository',
            'default': self.get_option('repo', group.project),
            'type': 'text',
            'readonly': True
        }] + fields + [{
            'name': 'assignee',
            'label': 'Assignee',
            'default': '',
            'type': 'select',
            'required': False,
            'choices': self.get_allowed_assignees(request, group)
        }]

    def get_link_existing_issue_fields(self, request, group, event, **kwargs):
        return [{
            'name': 'issue_id',
            'label': 'Issue',
            'default': '',
            'type': 'select',
            'has_autocomplete': True,
            'help': ('You can use any syntax supported by GitHub\'s '
                     '<a href="https://help.github.com/articles/searching-issues/" '
                     'target="_blank">issue search.</a>')
        }, {
            'name': 'comment',
            'label': 'Comment',
            'default': absolute_uri(group.get_absolute_url()),
            'type': 'textarea',
            'help': ('Leave blank if you don\'t want to '
                     'add a comment to the GitHub issue.'),
            'required': False
        }]

    def get_client(self, project, user):
        auth = self.get_auth_for_user(user=user)
        if auth is None:
            raise PluginError(ERR_UNAUTHORIZED)
        return GitHubClient(token=auth.tokens['access_token'])

    def handle_api_error(self, error):
        status = 400 if isinstance(error, PluginError) else 502
        return Response({
            'error_type': 'validation',
            'errors': {'__all__': self.message_from_error(error)},
        }, status=status)

    def message_from_error(self, exc):
        if isinstance(exc, ApiUnauthorized):
            return ERR_UNAUTHORIZED
        elif isinstance(exc, ApiError):
            if exc.code == 404:
                return (ERR_404)
            return ('Error Communicating with GitHub (HTTP %s): %s' % (
                exc.code,
                exc.json.get('message', 'unknown error') if exc.json else 'unknown error',
            ))
        else:
            return ERR_INTERNAL

    def raise_error(self, exc):
        if not isinstance(exc, ApiError):
            self.logger.exception(six.text_type(exc))
        raise PluginError(self.message_from_error(exc))

    def get_allowed_assignees(self, request, group):
        client = self.get_client(group.project, request.user)
        try:
            response = client.list_assignees(
                repo=self.get_option('repo', group.project),
            )
        except Exception as e:
            self.raise_error(e)

        users = tuple((u['login'], u['login']) for u in response)

        return (('', 'Unassigned'),) + users

    def create_issue(self, request, group, form_data, **kwargs):
        # TODO: support multiple identities via a selection input in the form?
        client = self.get_client(group.project, request.user)

        try:
            response = client.create_issue(
                repo=self.get_option('repo', group.project),
                data={
                    'title': form_data['title'],
                    'body': form_data['description'],
                    'assignee': form_data.get('assignee'),
                },
            )
        except Exception as e:
            self.raise_error(e)

        return response['number']

    def link_issue(self, request, group, form_data, **kwargs):
        comment = form_data.get('comment')
        if not comment:
            return

        client = self.get_client(group.project, request.user)
        try:
            client.create_comment(
                repo=self.get_option('repo', group.project),
                issue_id=form_data['issue_id'],
                data={
                    'body': comment,
                },
            )
        except Exception as e:
            self.raise_error(e)

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'GH-%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        # XXX: get_option may need tweaked in Sentry so that it can be pre-fetched in bulk
        repo = self.get_option('repo', group.project)

        return 'https://github.com/%s/issues/%s' % (repo, issue_id)

    def get_issue_title_by_id(self, request, group, issue_id):
        client = self.get_client(group.project, request.user)

        try:
            response = client.get_issue(
                repo=self.get_option('repo', group.project),
                issue_id=issue_id,
            )
        except Exception as e:
            return self.handle_api_error(e)

        return response['title']

    def view_autocomplete(self, request, group, **kwargs):
        field = request.GET.get('autocomplete_field')
        query = request.GET.get('autocomplete_query')
        if field != 'issue_id' or not query:
            return Response({'issue_id': []})

        repo = self.get_option('repo', group.project)
        client = self.get_client(group.project, request.user)

        try:
            response = client.search_issues(
                query=(u'repo:%s %s' % (repo, query)).encode('utf-8'),
            )
        except Exception as e:
            return self.handle_api_error(e)

        issues = [{
            'text': '(#%s) %s' % (i['number'], i['title']),
            'id': i['number']
        } for i in response.get('items', [])]

        return Response({field: issues})

    def get_configure_plugin_fields(self, request, project, **kwargs):
        return [{
            'name': 'repo',
            'label': 'Repository Name',
            'default': self.get_option('repo', project),
            'type': 'text',
            'placeholder': 'e.g. getsentry/sentry',
            'help': 'Enter your repository name, including the owner.'
        }]
