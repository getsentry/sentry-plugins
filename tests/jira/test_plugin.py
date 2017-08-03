from __future__ import absolute_import

import mock

from exam import fixture
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from sentry.testutils import TestCase
from sentry.utils import json

from sentry_plugins.jira.client import JIRAResponse
from sentry_plugins.jira.plugin import JiraPlugin

create_meta_response = {
    'expand':
    'projects',
    'projects': [
        {
            'expand':
            'issuetypes',
            'self':
            'https://getsentry.atlassian.net/rest/api/2/project/10000',
            'id':
            '10000',
            'key':
            'SEN',
            'name':
            'Sentry',
            'avatarUrls': {
                '48x48':
                'https://getsentry.atlassian.net/secure/projectavatar?avatarId=10324',
                '24x24':
                'https://getsentry.atlassian.net/secure/projectavatar?size=small&avatarId=10324',
                '16x16':
                'https://getsentry.atlassian.net/secure/projectavatar?size=xsmall&avatarId=10324',
                '32x32':
                'https://getsentry.atlassian.net/secure/projectavatar?size=medium&avatarId=10324'
            },
            'issuetypes': [
                {
                    'self':
                    'https://getsentry.atlassian.net/rest/api/2/issuetype/10002',
                    'id':
                    '10002',
                    'description':
                    'A task that needs to be done.',
                    'iconUrl':
                    'https://getsentry.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10318&avatarType=issuetype',
                    'name':
                    'Task',
                    'subtask':
                    False,
                    'expand':
                    'fields',
                    'fields': {
                        'summary': {
                            'required': True,
                            'schema': {
                                'type': 'string',
                                'system': 'summary',
                            },
                            'name': 'Summary',
                            'hasDefaultValue': False,
                            'operations': ['set']
                        },
                        'issuetype': {
                            'required':
                            True,
                            'schema': {
                                'type': 'issuetype',
                                'system': 'issuetype'
                            },
                            'name':
                            'Issue Type',
                            'hasDefaultValue':
                            False,
                            'operations': [],
                            'allowedValues': [
                                {
                                    'self':
                                    'https://getsentry.atlassian.net/rest/api/2/issuetype/10002',
                                    'id':
                                    '10002',
                                    'description':
                                    'A task that needs to be done.',
                                    'iconUrl':
                                    'https://getsentry.atlassian.net/secure/viewavatar?size=xsmall&avatarId=10318&avatarType=issuetype',
                                    'name':
                                    'Task',
                                    'subtask':
                                    False,
                                    'avatarId':
                                    10318,
                                }
                            ]
                        },
                        'components': {
                            'required': False,
                            'schema': {
                                'type': 'array',
                                'items': 'component',
                                'system': 'components',
                            },
                            'name': 'Component/s',
                            'hasDefaultValue': False,
                            'operations': ['add', 'set', 'remove'],
                            'allowedValues': [],
                        },
                        'description': {
                            'required': False,
                            'schema': {
                                'type': 'string',
                                'system': 'description',
                            },
                            'name': 'Description',
                            'hasDefaultValue': False,
                            'operations': ['set']
                        },
                        'project': {
                            'required':
                            True,
                            'schema': {
                                'type': 'project',
                                'system': 'project'
                            },
                            'name':
                            'Project',
                            'hasDefaultValue':
                            False,
                            'operations': ['set'],
                            'allowedValues': [
                                {
                                    'self':
                                    'https://getsentry.atlassian.net/rest/api/2/project/10000',
                                    'id': '10000',
                                    'key': 'SEN',
                                    'name': 'Sentry',
                                    'avatarUrls': {
                                        '48x48':
                                        'https://getsentry.atlassian.net/secure/projectavatar?avatarId=10324',
                                        '24x24':
                                        'https://getsentry.atlassian.net/secure/projectavatar?size=small&avatarId=10324',
                                        '16x16':
                                        'https://getsentry.atlassian.net/secure/projectavatar?size=xsmall&avatarId=10324',
                                        '32x32':
                                        'https://getsentry.atlassian.net/secure/projectavatar?size=medium&avatarId=10324',
                                    }
                                }
                            ]
                        },
                        'reporter': {
                            'required':
                            True,
                            'schema': {
                                'type': 'user',
                                'system': 'reporter',
                            },
                            'name':
                            'Reporter',
                            'autoCompleteUrl':
                            'https://getsentry.atlassian.net/rest/api/latest/user/search?username=',
                            'hasDefaultValue':
                            False,
                            'operations': ['set'],
                        },
                        'fixVersions': {
                            'required': False,
                            'schema': {
                                'type': 'array',
                                'items': 'version',
                                'system': 'fixVersions',
                            },
                            'name': 'Fix Version/s',
                            'hasDefaultValue': False,
                            'operations': ['set', 'add', 'remove'],
                            'allowedValues': [],
                        },
                        'priority': {
                            'required':
                            False,
                            'schema': {
                                'type': 'priority',
                                'system': 'priority',
                            },
                            'name':
                            'Priority',
                            'hasDefaultValue':
                            True,
                            'operations': ['set'],
                            'allowedValues': [
                                {
                                    'self':
                                    'https://getsentry.atlassian.net/rest/api/2/priority/1',
                                    'iconUrl':
                                    'https://getsentry.atlassian.net/images/icons/priorities/highest.svg',
                                    'name':
                                    'Highest',
                                    'id':
                                    '1'
                                },
                            ]
                        },
                        'customfield_10003': {
                            'required': False,
                            'schema': {
                                'type': 'array',
                                'items': 'string',
                                'custom': 'com.pyxis.greenhopper.jira:gh-sprint',
                                'customId': 10003,
                            },
                            'name': 'Sprint',
                            'hasDefaultValue': False,
                            'operations': ['set']
                        },
                        'labels': {
                            'required':
                            False,
                            'schema': {
                                'type': 'array',
                                'items': 'string',
                                'system': 'labels',
                            },
                            'name':
                            'Labels',
                            'autoCompleteUrl':
                            'https://getsentry.atlassian.net/rest/api/1.0/labels/suggest?query=',
                            'hasDefaultValue':
                            False,
                            'operations': ['add', 'set', 'remove'],
                        },
                        'attachment': {
                            'required': False,
                            'schema': {
                                'type': 'array',
                                'items': 'attachment',
                                'system': 'attachment',
                            },
                            'name': 'Attachment',
                            'hasDefaultValue': False,
                            'operations': [],
                        },
                        'assignee': {
                            'required':
                            False,
                            'schema': {
                                'type': 'user',
                                'system': 'assignee',
                            },
                            'name':
                            'Assignee',
                            'autoCompleteUrl':
                            'https://getsentry.atlassian.net/rest/api/latest/user/assignable/search?issueKey=null&username=',
                            'hasDefaultValue':
                            False,
                            'operations': ['set'],
                        }
                    }
                }
            ]
        }
    ]
}

issue_response = {
    'key': 'SEN-19',
    'id': '10708',
    'fields': {
        'summary': 'TypeError: \'set\' object has no attribute \'__getitem__\''
    }
}


class JiraPluginTest(TestCase):
    @fixture
    def plugin(self):
        return JiraPlugin()

    @fixture
    def request(self):
        return RequestFactory()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'jira'

    def test_get_issue_label(self):
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert self.plugin.get_issue_label(group, 'SEN-1') == 'SEN-1'

    def test_get_issue_url(self):
        self.plugin.set_option('instance_url', 'https://getsentry.atlassian.net', self.project)
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert self.plugin.get_issue_url(
            group, 'SEN-1'
        ) == 'https://getsentry.atlassian.net/browse/SEN-1'

    def test_is_configured(self):
        assert self.plugin.is_configured(None, self.project) is False
        self.plugin.set_option('default_project', 'SEN', self.project)
        assert self.plugin.is_configured(None, self.project) is True

    @mock.patch(
        'sentry_plugins.jira.client.JIRAClient.get_create_meta',
        mock.Mock(return_value=JIRAResponse(json.dumps(create_meta_response), 200))
    )
    @mock.patch(
        'sentry_plugins.jira.client.JIRAClient.create_issue',
        mock.Mock(return_value=JIRAResponse(json.dumps({
            'key': 'SEN-1'
        }), 200))
    )
    def test_create_issue(self):
        self.plugin.set_option('instance_url', 'https://getsentry.atlassian.net', self.project)
        group = self.create_group(message='Hello world', culprit='foo.bar')

        request = self.request.get('/')
        request.user = AnonymousUser()
        form_data = {
            'title': 'Hello',
            'description': 'Fix this.',
            'issuetype': 'bug',
            'project': 'SEN'
        }
        assert self.plugin.create_issue(request, group, form_data) == 'SEN-1'

    @mock.patch(
        'sentry_plugins.jira.client.JIRAClient.get_issue',
        mock.Mock(return_value=JIRAResponse(json.dumps(issue_response), 200))
    )
    def test_link_issue(self):
        self.plugin.set_option('instance_url', 'https://getsentry.atlassian.net', self.project)
        group = self.create_group(message='Hello world', culprit='foo.bar')

        request = self.request.get('/')
        request.user = AnonymousUser()
        form_data = {'issue_id': 'SEN-19'}
        assert self.plugin.link_issue(request, group,
                                      form_data)['title'] == issue_response['fields']['summary']

    def test_no_secrets(self):
        self.user = self.create_user('foo@example.com')
        self.org = self.create_organization(owner=self.user, name='Rowdy Tiger')
        self.team = self.create_team(organization=self.org, name='Mariachi Band')
        self.project = self.create_project(
            organization=self.org,
            team=self.team,
            name='Bengal',
        )
        self.login_as(self.user)
        self.plugin.set_option('password', 'abcdef', self.project)
        url = reverse(
            'sentry-api-0-project-plugin-details', args=[self.org.slug, self.project.slug, 'jira']
        )
        res = self.client.get(url)
        config = json.loads(res.content)['config']
        password_config = [item for item in config if item['name'] == 'password'][0]
        assert password_config.get('type') == 'secret'
        assert password_config.get('value') is None
        assert password_config.get('has_saved_value') is True
        assert password_config.get('prefix') == ''
