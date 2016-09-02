"""
pivotal.plugin
~~~~~~~~~~~~~

:copyright: (c) 2016 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from rest_framework.response import Response
from django.conf.urls import url
from django.utils.encoding import force_text
from sentry.plugins.bases.issue2 import IssuePlugin2, IssueGroupActionEndpoint, PluginError

import sentry_plugins
import pyvotal

GENERIC_ERROR = "Error communicating with Pivotal Tracker"


class PivotalPlugin(IssuePlugin2):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry/sentry'
    version = sentry_plugins.VERSION
    description = "Integrate Pivotal Tracker stories by linking a project and account."
    resource_links = [
        ('Bug Tracker', 'https://github.com/getsentry/sentry-plugins/issues'),
        ('Source', 'https://github.com/getsentry/sentry-plugins'),
    ]

    slug = 'pivotal'
    title = 'Pivotal Tracker'
    conf_title = title
    conf_key = 'pivotal'

    def get_group_urls(self):
        _patterns = super(PivotalPlugin, self).get_group_urls()
        _patterns.append(url(r'^autocomplete',
                             IssueGroupActionEndpoint.as_view(view_method_name='view_autocomplete',
                                                              plugin=self)))
        return _patterns

    def is_configured(self, request, project, **kwargs):
        return all(self.get_option(k, project) for k in ('token', 'project'))

    def get_api_client(self, project):
        return pyvotal.PTracker(token=self.get_option('token', project))

    def get_link_existing_issue_fields(self, request, group, event, **kwargs):
        return [{
            'name': 'issue_id',
            'label': 'Story',
            'default': '',
            'type': 'select',
            'has_autocomplete': True,
            'help': 'Search Pivotal Stories by name or description.'
        }, {
            'name': 'comment',
            'label': 'Comment',
            'default': group.get_absolute_url(),
            'type': 'textarea',
            'help': ('Leave blank if you don\'t want to '
                     'add a comment to the Pivotal story.'),
            'required': False
        }]

    def view_autocomplete(self, request, group, **kwargs):
        field = request.GET.get('autocomplete_field')
        query = request.GET.get('autocomplete_query')
        if field != 'issue_id' or not query:
            return Response({'issue_id': []})
        client = self.get_api_client(group.project)

        try:
            project = client.projects.get(self.get_option('project', group.project))
            stories = project.stories.all()
        except (pyvotal.exceptions.PyvotalException, pyvotal.exceptions.AccessDenied) as error:
            status = 400 if isinstance(error, PluginError) else 502
            return Response({'error_type': 'validation',
                     'errors': [{'__all__': GENERIC_ERROR}],
                     }, status=status)
        issues = []
        query = query.lower()
        for story in stories:
            if query in story.name.lower() or query in story.description.lower():
                issues.append({'text': '(#%s) %s)' % (story.id, story.name),
                               'id': story.id})
        return Response({field: issues})

    def link_issue(self, request, group, form_data, **kwargs):
        comment = form_data.get('comment')
        if not comment:
            return
        client = self.get_api_client(group.project)

        try:
            project = client.projects.get(self.get_option('project', group.project))
            story = project.stories.get(form_data['issue_id'])
            story.add_note(comment)
        except (pyvotal.exceptions.PyvotalException, pyvotal.exceptions.AccessDenied):
            raise PluginError(GENERIC_ERROR)

    def create_issue(self, request, group, form_data, **kwargs):
        client = self.get_api_client(group.project)
        story = client.Story()
        story.story_type = "bug"
        story.name = force_text(form_data['title'], errors='replace')
        story.description = force_text(form_data['description'], errors='replace')
        story.labels = "sentry"

        try:
            project = client.projects.get(self.get_option('project', group.project))
            story = project.stories.add(story)
        except (pyvotal.exceptions.PyvotalException, pyvotal.exceptions.AccessDenied):
            raise PluginError(GENERIC_ERROR)

        return story.id

    def get_issue_label(self, group, issue_id, **kwargs):
        return '#%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        return 'https://www.pivotaltracker.com/story/show/%s' % issue_id

    def get_issue_title_by_id(self, request, group, issue_id):
        client = self.get_api_client(group.project)
        project = client.projects.get(self.get_option('project', group.project))
        story = project.stories.get(issue_id)

        return story.name

    def get_configure_plugin_fields(self, request, project, **kwargs):
        return [{
            'name': 'token',
            'label': 'API Token',
            'default': self.get_option('token', project),
            'type': 'text',
            'placeholder': 'e.g. a9877d72b6d13b23410a7109b35e88bc',
            'help': 'Enter your API Token (found on <a href="https://www.pivotaltracker.com/profile">pivotaltracker.com/profile</a>).'},
            {
            'name': 'project',
            'label': 'Project ID',
            'default': self.get_option('project', project),
            'type': 'text',
            'placeholder': 'e.g. 639281',
            'help': 'Enter your project\'s numerical ID.'
        }]
