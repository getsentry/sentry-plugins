from __future__ import absolute_import

import logging
import six

from rest_framework.response import Response

from sentry.exceptions import InvalidIdentity, PluginError
from sentry.plugins.bases.issue2 import IssuePlugin2, IssueGroupActionEndpoint
from sentry.utils.http import absolute_uri

from sentry.plugins import providers
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

    def get_group_urls(self):
        return super(BitbucketPlugin, self).get_group_urls() + [
            (r'^autocomplete', IssueGroupActionEndpoint.as_view(
                view_method_name='view_autocomplete',
                plugin=self,
            )),
        ]

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

    def get_link_existing_issue_fields(self, request, group, event, **kwargs):
        return [{
            'name': 'issue_id',
            'label': 'Issue',
            'default': '',
            'type': 'select',
            'has_autocomplete': True
        }, {
            'name': 'comment',
            'label': 'Comment',
            'default': absolute_uri(group.get_absolute_url()),
            'type': 'textarea',
            'help': ('Leave blank if you don\'t want to '
                     'add a comment to the Bitbucket issue.'),
            'required': False
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

    def link_issue(self, request, group, form_data, **kwargs):
        client = self.get_client(request.user)
        repo = self.get_option('repo', group.project)
        try:
            issue = client.get_issue(
                repo=repo,
                issue_id=form_data['issue_id'],
            )
        except Exception as e:
            self.raise_error(e)

        comment = form_data.get('comment')
        if comment:
            try:
                client.create_comment(repo, issue['local_id'], {'content': comment})
            except Exception as e:
                self.raise_error(e)

        return {
            'title': issue['title']
        }

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

    def view_autocomplete(self, request, group, **kwargs):
        field = request.GET.get('autocomplete_field')
        query = request.GET.get('autocomplete_query')
        if field != 'issue_id' or not query:
            return Response({'issue_id': []})

        repo = self.get_option('repo', group.project)
        client = self.get_client(request.user)

        try:
            response = client.search_issues(repo, query.encode('utf-8'))
        except Exception as e:
            return Response({
                'error_type': 'validation',
                'errors': [{'__all__': self.message_from_error(e)}]
            }, status=400)

        issues = [{
            'text': '(#%s) %s' % (i['local_id'], i['title']),
            'id': i['local_id']
        } for i in response.get('issues', [])]

        return Response({field: issues})

class BitbucketRepositoryProvider(BitbucketPlugin, providers.RepositoryProvider):
    name = 'Bitbucket'
    auth_provider = 'bitbucket'
    logger = logging.getLogger('sentry.plugins.bitbucket')

    def get_config(self):
        return [{
            'name': 'name',
            'label': 'Repository Name',
            'type': 'text',
            'placeholder': 'e.g. getsentry/sentry',
            'help': 'Enter your repository name, including the owner.',
            'required': True,
        }]

    def validate_config(self, organization, config, actor=None):
        """
        ```
        if config['foo'] and not config['bar']:
            raise PluginError('You cannot configure foo with bar')
        return config
        ```
        """
        if config.get('name'):
            client = self.get_client(actor)
            try:
                repo = client.get_repo(config['name'])
            except Exception as e:
                self.raise_error(e)
            else:
                config['external_id'] = six.text_type(repo['id'])
        return config

    def get_webhook_secret(self, organization):
        lock = locks.get('bitbucket:webhook-secret:{}'.format(organization.id),
                         duration=60)
        with lock.acquire():
            # TODO(dcramer): get_or_create would be a useful native solution
            secret = OrganizationOption.objects.get_value(
                organization=organization,
                key='bitbucket:webhook_secret',
            )
            if secret is None:
                secret = uuid4().hex + uuid4().hex
                OrganizationOption.objects.set_value(
                    organization=organization,
                    key='bitbucket:webhook_secret',
                    value=secret,
                )
        return secret

    def create_repository(self, organization, data, actor=None):
        if actor is None:
            raise NotImplementedError('Cannot create a repository anonymously')

        client = self.get_client(actor)

        try:
            resp = client.create_hook(data['name'], {
                'name': 'web',
                'active': True,
                'events': ['push'],
                'config': {
                    'url': absolute_uri('/plugins/bitbucket/organizations/{}/webhook/'.format(organization.id)),
                    'content_type': 'json',
                    'secret': self.get_webhook_secret(organization),
                },
            })
        except Exception as e:
            self.raise_error(e)
        else:
            return {
                'name': data['name'],
                'external_id': data['external_id'],
                'url': 'https://bitbucket.org/{}'.format(data['name']),
                'config': {
                    'name': data['name'],
                    'webhook_id': resp['id'],
                }
            }

    def delete_repository(self, repo, actor=None):
        if actor is None:
            raise NotImplementedError('Cannot delete a repository anonymously')

        client = self.get_client(actor)
        try:
            client.delete_hook(repo.config['name'], repo.config['webhook_id'])
        except ApiError as exc:
            if exc.code == 404:
                return
            raise

    def _format_commits(self, repo, commit_list):
        return [{
            'id': c['sha'],
            'repository': repo.name,
            'author_email': c['commit']['author'].get('email'),
            'author_name': c['commit']['author'].get('name'),
            'message': c['commit']['message'],
        } for c in commit_list]

    def compare_commits(self, repo, start_sha, end_sha, actor=None):
        if actor is None:
            raise NotImplementedError('Cannot fetch commits anonymously')

        client = self.get_client(actor)
        # use config name because that is kept in sync via webhooks
        name = repo.config['name']
        if start_sha is None:
            try:
                res = client.get_last_commits(name, end_sha)
            except Exception as e:
                self.raise_error(e)
            else:
                return self._format_commits(repo, res[:10])
        else:
            try:
                res = client.compare_commits(name, start_sha, end_sha)
            except Exception as e:
                self.raise_error(e)
            else:
                return self._format_commits(repo, res['commits'])
