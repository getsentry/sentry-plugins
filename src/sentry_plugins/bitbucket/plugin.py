from __future__ import absolute_import

import six

from sentry.exceptions import InvalidIdentity, PluginError
from sentry.plugins.bases.issue2 import IssuePlugin2

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.exceptions import ApiError, ApiUnauthorized
from .client import BitbucketClient

ISSUE_TYPES = (
    ('bug', 'Bug'),
    ('enhancement', 'Enhancement'),
    ('proposal', 'Proposal'),
    ('task', 'Task'),
)

PRIORITIES = (
    ('trivial', 'Trivial',),
    ('minor', 'Minor',),
    ('major', 'Major'),
    ('critical', 'Critical'),
    ('blocker', 'Blocker'),
)

ERR_INTERNAL = (
    'An internal error occurred with the integration and '
    'the Sentry team has been notified'
)

ERR_UNAUTHORIZED = (
    'Unauthorized: either your access token was invalid or '
    'you do not have access'
)

ERR_404 = ('Bitbucket returned a 404. Please make sure that '
           'the repo exists, you have access to it, and it has '
           'issue tracking enabled.')


class BitbucketPlugin(CorePluginMixin, IssuePlugin2):
    description = 'Integrate Bitbucket issues by linking a repository to a project.'
    slug = 'bitbucket'
    title = 'Bitbucket'
    conf_title = title
    conf_key = 'bitbucket'
    auth_provider = 'bitbucket'
    allowed_actions = ('create', 'unlink')

    def is_configured(self, request, project, **kwargs):
        return bool(self.get_option('repo', project))

    def get_new_issue_fields(self, request, group, event, **kwargs):
        fields = super(BitbucketPlugin, self).get_new_issue_fields(request, group, event, **kwargs)
        return [{
            'name': 'repo',
            'label': 'Bitbucket Repository',
            'default': self.get_option('repo', group.project),
            'type': 'text',
            'readonly': True
        }] + fields + [{
            'name': 'issue_type',
            'label': 'Issue type',
            'default': ISSUE_TYPES[0][0],
            'type': 'select',
            'choices': ISSUE_TYPES
        }, {
            'name': 'priority',
            'label': 'Priority',
            'default': PRIORITIES[0][0],
            'type': 'select',
            'choices': PRIORITIES
        }]

    def get_client(self, user):
        auth = self.get_auth_for_user(user=user)
        if auth is None:
            raise PluginError('You still need to associate an identity with Bitbucket.')
        return BitbucketClient(auth)

    def message_from_error(self, exc):
        if isinstance(exc, ApiUnauthorized):
            return ERR_UNAUTHORIZED
        elif isinstance(exc, ApiError):
            if exc.code == 404:
                return ERR_404
            return ('Error Communicating with Bitbucket (HTTP %s): %s' % (
                exc.code,
                exc.json.get('message', 'unknown error') if exc.json else 'unknown error',
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
                repo=self.get_option('repo', group.project),
                data=form_data
            )
        except Exception as e:
            self.raise_error(e)

        return response['local_id']

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'Bitbucket-%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        repo = self.get_option('repo', group.project)
        return 'https://bitbucket.org/%s/issue/%s/' % (repo, issue_id)

    def get_configure_plugin_fields(self, request, project, **kwargs):
        return [{
            'name': 'repo',
            'label': 'Repository Name',
            'default': self.get_option('repo', project),
            'type': 'text',
            'placeholder': 'e.g. getsentry/sentry',
            'help': 'Enter your repository name, including the owner.'
        }]
