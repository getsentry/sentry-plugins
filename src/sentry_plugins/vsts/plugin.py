
""" A plugin to incorporate work-item creation in VSTS
easily out of issues detected from Sentry.io """

from __future__ import absolute_import

from django.utils.html import format_html
from rest_framework.response import Response

from sentry.api.serializers.models.plugin import PluginSerializer
from sentry.models import Activity, Event, GroupMeta
from sentry.signals import issue_tracker_used
from sentry.utils.http import absolute_uri

from sentry.plugins.bases.issue2 import IssueTrackingPlugin2

from .mixins import VisualStudioMixin
from .repository_provider import VisualStudioRepositoryProvider


class VstsPlugin(VisualStudioMixin, IssueTrackingPlugin2):
    description = 'Integrate Visual Studio Team Services work items by linking a project.'
    slug = 'vsts'
    conf_key = slug
    auth_provider = 'visualstudio'

    issue_fields = frozenset(['id', 'title', 'url'])

    def get_configure_plugin_fields(self, request, project, **kwargs):
        # TODO(dcramer): Both Account and Project can query the API an access
        # token, and could likely be moved to the 'Create Issue' form
        return [
            {
                'name': 'instance',
                'label': 'Instance',
                'type': 'text',
                'placeholder': 'example.visualstudio.com',
                'required': True,
                'help': 'VS Team Services account ({account}.visualstudio.com) or TFS server ({server:port}).',
            },
            {
                'name': 'default_project',
                'label': 'Default Project Name',
                'type': 'text',
                'placeholder': 'MyProject',
                'required': False,
                'help': (
                    'Enter the Visual Studio Team Services project name that you wish '
                    'to use as a default for new work items'
                ),
            },
        ]

    def is_configured(self, request, project, **kwargs):
        for o in ('instance',):
            if not bool(self.get_option(o, project)):
                return False
        return True

    def get_group_description(self, request, group, event):
        return self.get_group_body(request, group, event)

    def get_issue_label(self, group, issue, **kwargs):
        return 'Bug {}'.format(issue['id'])

    def get_issue_url(self, group, issue, **kwargs):
        """
        Given an issue_id (string) return an absolute URL to the issue's
        details page.
        """
        return issue['url']

    def get_new_issue_fields(self, request, group, event, **kwargs):
        fields = super(VstsPlugin, self).get_new_issue_fields(request, group, event, **kwargs)
        client = self.get_client(request.user)
        instance = self.get_option('instance', group.project)

        try:
            projects = client.get_projects(instance)
        except Exception as e:
            self.raise_error(e, identity=client.auth)

        return [
            {
                'name': 'project',
                'label': 'Project',
                'default': self.get_option('default_project', group.project),
                'type': 'text',
                'choices': [i['name'] for i in projects['value']],
                'required': True,
            }
        ] + fields

    def get_link_existing_issue_fields(self, request, group, event, **kwargs):
        return [
            {
                'name': 'item_id',
                'label': 'Work Item ID',
                'default': '',
                'type': 'text',
            },
            {
                'name': 'comment',
                'label': 'Comment',
                'default': 'I\'ve identified this issue in Sentry: {}'.format(
                    absolute_uri(group.get_absolute_url()),
                ),
                'type': 'textarea',
                'help': ('Leave blank if you don\'t want to add a comment'),
                'required': False
            }
        ]

    def create_issue(self, request, group, form_data, **kwargs):
        """
        Creates the issue on the remote service and returns an issue ID.
        """
        instance = self.get_option('instance', group.project)
        project = (
            form_data.get('project') or
            self.get_option('default_project', group.project)
        )

        client = self.get_client(request.user)

        title = form_data['title']
        description = form_data['description']
        link = absolute_uri(group.get_absolute_url())
        try:
            created_item = client.create_work_item(instance, project, title, description, link)
        except Exception as e:
            self.raise_error(e, identity=client.auth)

        return {
            'id': created_item['id'],
            'url': created_item['_links']['html']['href'],
            'title': title,
        }

    def link_issue(self, request, group, form_data, **kwargs):
        client = self.get_client(request.user)
        instance = self.get_option('instance', group.project)
        try:
            work_item = client.update_work_item(
                instance=instance,
                id=form_data['item_id'],
                link=absolute_uri(group.get_absolute_url()),
                comment=form_data.get('comment'),
            )
        except Exception as e:
            self.raise_error(e, identity=client.auth)

        return {
            'id': work_item['id'],
            'url': work_item['_links']['html']['href'],
            'title': work_item['fields']['System.Title'],
        }

    def build_issue(self, group):
        conf_key = self.get_conf_key()
        issue = {}
        for key in self.issue_fields:
            issue[key] = GroupMeta.objects.get_value(group, '{}:issue_{}'.format(
                conf_key,
                key,
            ), None)
        if not any(issue.values()):
            return None
        return issue

    def has_linked_issue(self, group):
        return bool(self.build_issue(group))

    def unlink_issue(self, request, group, issue, **kwargs):
        conf_key = self.get_conf_key()
        # TODO(dcramer): these shouldn't be hardcoded here
        for key in self.issue_fields:
            GroupMeta.objects.unset_value(group, '{}:issue_{}'.format(conf_key, key))
        return self.redirect(group.get_absolute_url())

    def view_create(self, request, group, **kwargs):
        auth_errors = self.check_config_and_auth(request, group)
        if auth_errors:
            return Response(auth_errors, status=400)

        event = group.get_latest_event()
        Event.objects.bind_nodes([event], 'data')
        try:
            fields = self.get_new_issue_fields(request, group, event, **kwargs)
        except Exception as e:
            return self.handle_api_error(e)
        if request.method == 'GET':
            return Response(fields)

        errors = self.validate_form(fields, request.DATA)
        if errors:
            return Response({'error_type': 'validation', 'errors': errors}, status=400)

        try:
            issue = self.create_issue(
                group=group,
                form_data=request.DATA,
                request=request,
            )
        except Exception as e:
            return self.handle_api_error(e)

        conf_key = self.get_conf_key()
        for key in self.issue_fields:
            meta_name = '{}:issue_{}'.format(conf_key, key)
            if key in issue:
                GroupMeta.objects.set_value(group, meta_name, issue[key])
            else:
                GroupMeta.objects.unset_value(group, meta_name)

        issue_information = {
            'title': request.DATA['title'],
            'provider': self.get_title(),
            'location': self.get_issue_url(group, issue),
            'label': self.get_issue_label(group=group, issue=issue),
        }
        Activity.objects.create(
            project=group.project,
            group=group,
            type=Activity.CREATE_ISSUE,
            user=request.user,
            data=issue_information,
        )

        issue_tracker_used.send(
            plugin=self, project=group.project, user=request.user,
            sender=type(self)
        )
        return Response({'issue_url': self.get_issue_url(group=group, issue=issue)})

    def view_link(self, request, group, **kwargs):
        auth_errors = self.check_config_and_auth(request, group)
        if auth_errors:
            return Response(auth_errors, status=400)
        event = group.get_latest_event()
        Event.objects.bind_nodes([event], 'data')

        try:
            fields = self.get_link_existing_issue_fields(request, group, event, **kwargs)
        except Exception as e:
            return self.handle_api_error(e)
        if request.method == 'GET':
            return Response(fields)
        errors = self.validate_form(fields, request.DATA)
        if errors:
            return Response({'error_type': 'validation', 'errors': errors}, status=400)

        try:
            issue = self.link_issue(
                group=group,
                form_data=request.DATA,
                request=request,
            )
        except Exception as e:
            return self.handle_api_error(e)

        conf_key = self.get_conf_key()
        for key in self.issue_fields:
            meta_name = '{}:issue_{}'.format(conf_key, key)
            if key in issue:
                GroupMeta.objects.set_value(group, meta_name, issue[key])
            else:
                GroupMeta.objects.unset_value(group, meta_name)

        issue_information = {
            'title': issue['title'],
            'provider': self.get_title(),
            'location': self.get_issue_url(group, issue),
            'label': self.get_issue_label(group=group, issue=issue),
        }
        Activity.objects.create(
            project=group.project,
            group=group,
            type=Activity.CREATE_ISSUE,
            user=request.user,
            data=issue_information,
        )
        return Response({'message': 'Successfully linked issue.'})

    def view_unlink(self, request, group, **kwargs):
        auth_errors = self.check_config_and_auth(request, group)
        if auth_errors:
            return Response(auth_errors, status=400)
        issue = self.build_issue(group)
        if issue and 'unlink' in self.allowed_actions:
            self.unlink_issue(request, group, issue)
            return Response({'message': 'Successfully unlinked issue.'})
        return Response({'message': 'No issues to unlink.'}, status=400)

    def plugin_issues(self, request, group, plugin_issues, **kwargs):
        if not self.is_configured(request=request, project=group.project):
            return plugin_issues

        item = {
            'slug': self.slug,
            'allowed_actions': self.allowed_actions,
            'title': self.get_title()
        }
        issue = self.build_issue(group)
        if issue:
            item['issue'] = {
                'issue_id': issue.get('id'),
                'url': self.get_issue_url(group=group, issue=issue),
                'label': self.get_issue_label(group=group, issue=issue),
            }

        item.update(PluginSerializer(group.project).serialize(self, None, request.user))
        plugin_issues.append(item)
        return plugin_issues

    # TODO: should we get rid of this (move it to react?)
    def tags(self, request, group, tag_list, **kwargs):
        if not self.is_configured(request=request, project=group.project):
            return tag_list

        issue = self.build_issue(group)
        if not issue:
            return tag_list

        tag_list.append(
            format_html(
                '<a href="{}">{}</a>',
                self.get_issue_url(group=group, issue=issue),
                self.get_issue_label(group=group, issue=issue),
            )
        )

        return tag_list

    def setup(self, bindings):
        bindings.add('repository.provider', VisualStudioRepositoryProvider, id='visualstudio')
