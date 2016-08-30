from __future__ import absolute_import

import requests
import six

from django.conf.urls import url
from rest_framework.response import Response
from six.moves.urllib.parse import urlencode

from sentry.plugins.bases.issue2 import IssuePlugin2, IssueGroupActionEndpoint, PluginError
from sentry.http import safe_urlopen, safe_urlread
from sentry.utils import json
from sentry.utils.http import absolute_uri

import sentry_plugins


class GitHubPlugin(IssuePlugin2):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry/sentry'
    version = sentry_plugins.VERSION
    description = "Integrate GitHub issues by linking a repository to a project."
    resource_links = [
        ('Bug Tracker', 'https://github.com/getsentry/sentry-plugins/issues'),
        ('Source', 'https://github.com/getsentry/sentry-plugins'),
    ]

    slug = 'github'
    title = 'GitHub'
    conf_title = title
    conf_key = 'github'
    auth_provider = 'github'

    def get_group_urls(self):
        _patterns = super(GitHubPlugin, self).get_group_urls()
        _patterns.append(url(r'^autocomplete',
                             IssueGroupActionEndpoint.as_view(view_method_name='view_autocomplete',
                                                              plugin=self)))
        return _patterns

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

    def handle_api_error(self, error):
        msg = u'Error communicating with GitHub: %s' % error
        status = 400 if isinstance(error, PluginError) else 502
        return Response({
            'error_type': 'validation',
            'errors': {'__all__': msg},
        }, status=status)

    def get_allowed_assignees(self, request, group):
        try:
            _url = self.build_api_url(group, 'assignees')
            req = self.make_api_request(request.user, _url)
            body = safe_urlread(req)
        except (requests.RequestException, PluginError) as e:
            raise PluginError(u'Error communicating with GitHub: %s' % e)

        try:
            json_resp = json.loads(body)
        except ValueError as e:
            raise PluginError(u'Error communicating with GitHub: %s' % e)

        if req.status_code > 399:
            raise PluginError(u'Error communicating with GitHub: %s' % json_resp.get('message', ''))

        users = tuple((u['login'], u['login']) for u in json_resp)

        return (('', 'Unassigned'),) + users

    def build_api_url(self, group, github_api, query_params=None):
        repo = self.get_option('repo', group.project)

        _url = 'https://api.github.com/repos/%s/%s' % (repo, github_api)

        if query_params:
            _url = '%s?%s' % (_url, urlencode(query_params))

        return _url

    def make_api_request(self, user, _url, json_data=None):
        auth = self.get_auth_for_user(user=user)
        if auth is None:
            raise PluginError('You have not yet associated GitHub with your account.')

        req_headers = {
            'Authorization': 'token %s' % auth.tokens['access_token'],
        }
        return safe_urlopen(_url, json=json_data, headers=req_headers, allow_redirects=True)

    def create_issue(self, request, group, form_data, **kwargs):
        # TODO: support multiple identities via a selection input in the form?
        json_data = {
            "title": form_data['title'],
            "body": form_data['description'],
            "assignee": form_data.get('assignee'),
        }

        try:
            _url = self.build_api_url(group, 'issues')
            req = self.make_api_request(request.user, _url, json_data=json_data)
            body = safe_urlread(req)
        except requests.RequestException as e:
            msg = six.text_type(e)
            raise PluginError('Error communicating with GitHub: %s' % (msg,))

        try:
            json_resp = json.loads(body)
        except ValueError as e:
            msg = six.text_type(e)
            raise PluginError('Error communicating with GitHub: %s' % (msg,))

        if req.status_code > 399:
            raise PluginError(json_resp['message'])

        return json_resp['number']

    def link_issue(self, request, group, form_data, **kwargs):
        comment = form_data.get('comment')
        if not comment:
            return
        _url = '%s/%s/comments' % (self.build_api_url(group, 'issues'), form_data['issue_id'])
        try:
            req = self.make_api_request(request.user, _url, json_data={'body': comment})
            body = safe_urlread(req)
        except requests.RequestException as e:
            msg = six.text_type(e)
            raise PluginError('Error communicating with GitHub: %s' % (msg,))

        try:
            json_resp = json.loads(body)
        except ValueError as e:
            msg = six.text_type(e)
            raise PluginError('Error communicating with GitHub: %s' % (msg,))

        if req.status_code > 399:
            raise PluginError(json_resp['message'])

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'GH-%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        # XXX: get_option may need tweaked in Sentry so that it can be pre-fetched in bulk
        repo = self.get_option('repo', group.project)

        return 'https://github.com/%s/issues/%s' % (repo, issue_id)

    def get_issue_title_by_id(self, request, group, issue_id):
        _url = '%s/%s' % (self.build_api_url(group, 'issues'), issue_id)
        req = self.make_api_request(request.user, _url)

        body = safe_urlread(req)
        json_resp = json.loads(body)
        return json_resp['title']

    def view_autocomplete(self, request, group, **kwargs):
        field = request.GET.get('autocomplete_field')
        query = request.GET.get('autocomplete_query')
        if field != 'issue_id' or not query:
            return Response({'issue_id': []})

        repo = self.get_option('repo', group.project)
        query = (u'repo:%s %s' % (repo, query)).encode('utf-8')
        _url = 'https://api.github.com/search/issues?%s' % urlencode({'q': query})

        try:
            req = self.make_api_request(request.user, _url)
            body = safe_urlread(req)
        except (requests.RequestException, PluginError) as e:
            return self.handle_api_error(e)

        try:
            json_resp = json.loads(body)
        except ValueError as e:
            return self.handle_api_error(e)

        issues = [{
            'text': '(#%s) %s' % (i['number'], i['title']),
            'id': i['number']
        } for i in json_resp.get('items', [])]

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
