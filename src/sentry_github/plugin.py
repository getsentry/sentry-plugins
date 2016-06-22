"""
sentry_github.plugin
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import requests
from urllib import urlencode
from django import forms
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from sentry.plugins.base import JSONResponse
from sentry.plugins.bases.issue import IssuePlugin, NewIssueForm
from sentry.http import safe_urlopen, safe_urlread
from sentry.utils import json
from sentry.utils.http import absolute_uri

import sentry_github


class GitHubOptionsForm(forms.Form):
    repo = forms.CharField(
        label=_('Repository Name'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. getsentry/sentry'}),
        help_text=_('Enter your repository name, including the owner.'))
    endpoint = forms.CharField(
        label=_('GitHub API Endpoint'),
        widget=forms.TextInput(attrs={'placeholder': 'https://api.github.com'}),
        initial='https://api.github.com',
        help_text=_('Enter the base URL to the GitHub API.'))
    github_url = forms.CharField(
        label=_('GitHub Base URL'),
        widget=forms.TextInput(attrs={'placeholder': 'https://github.com'}),
        initial='https://github.com',
        help_text=_('Enter the base URL to the GitHub for generating issue links.'))

    def clean_endpoint(self):
        data = self.cleaned_data['endpoint']
        return data.rstrip('/')

    def clean_github_url(self):
        data = self.cleaned_data['github_url']
        return data.rstrip('/')


class GitHubNewIssueForm(NewIssueForm):
    assignee = forms.ChoiceField(choices=tuple(), required=False)

    def __init__(self, assignee_choices, *args, **kwargs):
        super(GitHubNewIssueForm, self).__init__(*args, **kwargs)
        self.fields['assignee'].choices = assignee_choices


class GitHubExistingIssueForm(forms.Form):
    issue_id = forms.CharField(
        label=_('Issue'),
        widget=forms.TextInput(attrs={'class': 'issue-selector'}),
        help_text=mark_safe(_('You can use any syntax supported by GitHub\'s '
                              '<a href="https://help.github.com/articles/searching-issues/" '
                              'target="_blank">issue search</a>.')))
    comment = forms.CharField(
        label=_('GitHub Comment'),
        widget=forms.Textarea,
        required=False,
        help_text=_('Leave blank if you don\'t want to add a comment to the GitHub issue'))


class GitHubPlugin(IssuePlugin):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry/sentry'
    version = sentry_github.VERSION
    new_issue_form = GitHubNewIssueForm
    link_issue_form = GitHubExistingIssueForm
    description = "Integrate GitHub issues by linking a repository to a project."
    resource_links = [
        ('Bug Tracker', 'https://github.com/getsentry/sentry-github/issues'),
        ('Source', 'https://github.com/getsentry/sentry-github'),
    ]

    slug = 'github'
    title = _('GitHub')
    conf_title = title
    conf_key = 'github'
    project_conf_form = GitHubOptionsForm
    auth_provider = 'github'
    create_issue_template = 'sentry_github/create_github_issue.html'
    can_unlink_issues = True
    can_link_existing_issues = True

    def is_configured(self, request, project, **kwargs):
        return bool(self.get_option('repo', project))

    def get_new_issue_title(self, **kwargs):
        return 'Link GitHub Issue'

    def get_unlink_issue_title(self, **kwargs):
        return 'Unlink GitHub Issue'

    def get_new_issue_read_only_fields(self, **kwargs):
        group = kwargs.get('group')
        if group:
            return [{'label': 'Github Repository', 'value': self.get_option('repo', group.project)}]
        return []

    def handle_api_error(self, request, error):
        msg = _('Error communicating with GitHub: %s') % error
        messages.add_message(request, messages.ERROR, msg)

    def get_allowed_assignees(self, request, group):
        try:
            url = self.build_api_url(group, 'assignees')
            req = self.make_api_request(request, url)
            body = safe_urlread(req)
        except requests.RequestException as e:
            msg = unicode(e)
            self.handle_api_error(request, msg)
            return tuple()

        try:
            json_resp = json.loads(body)
        except ValueError as e:
            msg = unicode(e)
            self.handle_api_error(request, msg)
            return tuple()

        if req.status_code > 399:
            self.handle_api_error(request, json_resp.get('message', ''))
            return tuple()

        users = tuple((u['login'], u['login']) for u in json_resp)

        return (('', 'Unassigned'),) + users

    def get_initial_link_form_data(self, request, group, event, **kwargs):
        return {'comment': absolute_uri(group.get_absolute_url())}

    def get_new_issue_form(self, request, group, event, **kwargs):
        """
        Return a Form for the "Create new issue" page.
        """
        return self.new_issue_form(self.get_allowed_assignees(request, group),
                                   request.POST or None,
                                   initial=self.get_initial_form_data(request, group, event))

    def build_api_url(self, group, github_api, query_params=None):
        repo = self.get_option('repo', group.project)
        endpoint = self.get_option('endpoint', group.project) or 'https://api.github.com'

        url = '%s/repos/%s/%s' % (endpoint, repo, github_api,)

        if query_params:
            url = '%s?%s' % (url, urlencode(query_params))

        return url

    def make_api_request(self, request, url, json_data=None):
        auth = self.get_auth_for_user(user=request.user)
        if auth is None:
            raise forms.ValidationError(_('You have not yet associated GitHub with your account.'))

        req_headers = {
            'Authorization': 'token %s' % auth.tokens['access_token'],
        }
        return safe_urlopen(url, json=json_data, headers=req_headers)

    def create_issue(self, request, group, form_data, **kwargs):
        # TODO: support multiple identities via a selection input in the form?
        json_data = {
            "title": form_data['title'],
            "body": form_data['description'],
            "assignee": form_data.get('assignee'),
        }

        try:
            url = self.build_api_url(group, 'issues')
            req = self.make_api_request(request, url, json_data=json_data)
            body = safe_urlread(req)
        except requests.RequestException as e:
            msg = unicode(e)
            raise forms.ValidationError(_('Error communicating with GitHub: %s') % (msg,))

        try:
            json_resp = json.loads(body)
        except ValueError as e:
            msg = unicode(e)
            raise forms.ValidationError(_('Error communicating with GitHub: %s') % (msg,))

        if req.status_code > 399:
            raise forms.ValidationError(json_resp['message'])

        return json_resp['number']

    def link_issue(self, request, group, form_data, **kwargs):
        comment = form_data.get('comment')
        if not comment:
            return
        url = '%s/%s/comments' % (self.build_api_url(group, 'issues'), form_data['issue_id'])
        try:
            req = self.make_api_request(request, url, json_data={'body': comment})
            body = safe_urlread(req)
        except requests.RequestException as e:
            msg = unicode(e)
            raise forms.ValidationError(_('Error communicating with GitHub: %s') % (msg,))

        try:
            json_resp = json.loads(body)
        except ValueError as e:
            msg = unicode(e)
            raise forms.ValidationError(_('Error communicating with GitHub: %s') % (msg,))

        if req.status_code > 399:
            raise forms.ValidationError(json_resp['message'])

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'GH-%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        # XXX: get_option may need tweaked in Sentry so that it can be pre-fetched in bulk
        repo = self.get_option('repo', group.project)
        github_url = self.get_option('github_url', group.project) or 'https://github.com'

        return '%s/%s/issues/%s' % (github_url, repo, issue_id)

    def get_issue_title_by_id(self, request, group, issue_id):
        url = '%s/%s' % (self.build_api_url(group, 'issues'), issue_id)
        req = self.make_api_request(request, url)

        body = safe_urlread(req)
        json_resp = json.loads(body)
        return json_resp['title']

    def view(self, request, group, **kwargs):
        if request.GET.get('autocomplete_query'):
            query = request.GET.get('q')
            if not query:
                return JSONResponse({'issues': []})
            repo = self.get_option('repo', group.project)
            query = 'repo:%s %s' % (repo, query)
            endpoint = self.get_option('endpoint', group.project) or 'https://api.github.com'
            url = '%s/search/issues?%s' % (endpoint, urlencode({'q': query}))

            try:
                req = self.make_api_request(request, url)
                body = safe_urlread(req)
            except requests.RequestException as e:
                msg = unicode(e)
                self.handle_api_error(request, msg)
                return JSONResponse({}, status_code=502)

            try:
                json_resp = json.loads(body)
            except ValueError as e:
                msg = unicode(e)
                self.handle_api_error(request, msg)
                return JSONResponse({}, status_code=502)

            issues = [{
                'text': '(#%s) %s' % (i['number'], i['title']),
                'id': i['number']
            } for i in json_resp.get('items', [])]
            return JSONResponse({'issues': issues})

        return super(GitHubPlugin, self).view(request, group, **kwargs)
