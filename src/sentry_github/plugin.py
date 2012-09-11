"""
sentry_github.plugin
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django import forms
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _
from sentry.plugins.bases.issue import IssuePlugin

import sentry_github
import urllib2


class GitHubOptionsForm(forms.Form):
    # TODO: validate repo?
    repo = forms.CharField(label=_('Repository Name'),
        widget=forms.TextInput(attrs={'class': 'span3', 'placeholder': 'e.g. getsentry/sentry'}),
        help_text=_('Enter your repository name, including the owner.'))


class GitHubPlugin(IssuePlugin):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry/sentry'
    version = sentry_github.VERSION
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

    def is_configured(self, request, project, **kwargs):
        return bool(self.get_option('repo', project))

    def get_new_issue_title(self, **kwargs):
        return 'Create GitHub Issue'

    def create_issue(self, request, group, form_data, **kwargs):
        # TODO: support multiple identities via a selection input in the form?
        auth = self.get_auth_for_user(user=request.user)
        if auth is None:
            raise forms.ValidationError(_('You have not yet associated GitHub with your account.'))

        repo = self.get_option('repo', group.project)

        url = 'https://api.github.com/repos/%s/issues' % (repo,)

        data = simplejson.dumps({
          "title": form_data['title'],
          "body": form_data['description'],
          # "assignee": form_data['asignee'],
          # "milestone": 1,
          # "labels": [
          #   "Label1",
          #   "Label2"
          # ]
        })

        req = urllib2.Request(url, data)
        req.add_header('User-Agent', 'sentry-github/%s' % self.version)
        req.add_header('Authorization', 'token %s' % auth.tokens['access_token'])
        req.add_header('Content-Type', 'application/json')

        try:
            resp = urllib2.urlopen(req)
        except Exception, e:
            if isinstance(e, urllib2.HTTPError):
                msg = e.read()
                if 'application/json' in e.headers['Content-Type']:
                    try:
                        msg = simplejson.loads(msg)
                        msg = msg['message']
                    except Exception:
                        # We failed, but we still want to report the original error
                        pass
            else:
                msg = unicode(e)
            raise forms.ValidationError(_('Error communicating with GitHub: %s') % (msg,))

        try:
            data = simplejson.load(resp)
        except Exception, e:
            raise forms.ValidationError(_('Error decoding response from GitHub: %s') % (e,))

        return data['number']

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'GH-%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        # XXX: get_option may need tweaked in Sentry so that it can be pre-fetched in bulk
        repo = self.get_option('repo', group.project)

        return 'https://github.com/%s/issues/%s' % (repo, issue_id)
