from __future__ import absolute_import

from django import forms
from django.utils.translation import ugettext_lazy as _
from requests.exceptions import RequestException
from rest_framework.response import Response

from sentry.plugins.bases.issue2 import IssuePlugin2, IssueGroupActionEndpoint, PluginError
from sentry.utils.http import absolute_uri

from sentry_plugins.base import CorePluginMixin

from .client import TrelloClient

SETUP_URL = 'https://github.com/damianzaremba/sentry-trello/blob/master/HOW_TO_SETUP.md'  # NOQA

ISSUES_URL = 'https://github.com/damianzaremba/sentry-trello/issues'

EMPTY = (('', ''),)


# class TrelloSettingsForm(forms.Form):
#     key = forms.CharField(label=_('Trello API Key'))
#     token = forms.CharField(label=_('Trello API Token'))
#     organization = forms.CharField(label=_('Organization to add a card to'),
#                                    max_length=50, required=False)

#     def __init__(self, *args, **kwargs):
#         super(TrelloSettingsForm, self).__init__(*args, **kwargs)
#         initial = kwargs['initial']

#         organizations = ()

#         if initial.get('key'):
#             trello = TrelloClient(initial.get('key'), initial.get('token'))
#             try:
#                 organizations = EMPTY + trello.organizations_to_options()
#             except RequestException:
#                 disabled = True
#             else:
#                 disabled = False
#         else:
#             disabled = True

#         if disabled:
#             attrs = {'disabled': 'disabled'}
#             help_text = _('Set correct key and token and save before')
#         else:
#             attrs = None
#             help_text = None

#         self.fields['organization'].widget = forms.Select(
#             attrs=attrs,
#             choices=organizations,
#         )
#         self.fields['organization'].help_text = help_text


# class TrelloForm(NewIssueForm):
#     title = forms.CharField(
#         label=_('Title'), max_length=200,
#         widget=forms.TextInput(attrs={'class': 'span9'}))
#     description = forms.CharField(
#         label=_('Description'),
#         widget=forms.Textarea(attrs={'class': 'span9'}))
#     trello_board = forms.CharField(label=_('Board'), max_length=50)
#     trello_list = forms.CharField(label=_('List'), max_length=50)

#     def __init__(self, data=None, initial=None):
#         super(TrelloForm, self).__init__(data=data, initial=initial)
#         self.fields['trello_board'].widget = forms.Select(
#             choices=EMPTY + initial.get('boards', ())
#         )
#         self.fields['trello_list'].widget = forms.Select(
#             attrs={'disabled': True},
#             choices=initial.get('list', ()),
#         )


class TrelloPlugin(CorePluginMixin, IssuePlugin2):
    title = 'Trello'
    conf_title = title
    description = 'Create Trello cards on exceptions.'
    slug = 'trello'
    conf_key = 'trello'

    asset_key = slug
    assets = [
        'dist/trello.js',
    ]

    def get_group_urls(self):
        return super(TrelloPlugin, self).get_group_urls() + [
            (r'^autocomplete', IssueGroupActionEndpoint.as_view(
                view_method_name='view_autocomplete',
                plugin=self,
            )),
        ]

    def _get_group_description(self, request, group, event):
        """
        Return group description in markdown-compatible format.

        This overrides an internal method to IssuePlugin.
        """
        output = [
            absolute_uri(group.get_absolute_url()),
        ]
        body = self._get_group_body(request, group, event)
        if body:
            output.extend([
                '',
                '\n'.join('    ' + line for line in body.splitlines()),
            ])
        return '\n'.join(output)

    def is_configured(self, request, project, **kwargs):
        return all((
            self.get_option(key, project)
            for key in ('key', 'token')
        ))

    def get_client(self, project):
        return TrelloClient(
            apikey=self.get_option('key', project),
            token=self.get_option('token', project),
        )

    def view_autocomplete(self, request, group, **kwargs):
        if request.GET.get('action', '') != 'lists':
            return Response({})
        board_id = request.GET['board_id']
        trello = self.get_client(group.project)
        lists = trello.get_board_list(board_id, fields='name')
        return Response({'result': lists})

    def get_initial_form_data(self, request, group, event, **kwargs):
        initial = super(TrelloPlugin, self).get_initial_form_data(
            request, group, event, **kwargs)
        trello = self.get_client(group.project)
        organization = self.get_option('organization', group.project)
        options = {}
        if organization:
            options['organization'] = organization
        try:
            boards = trello.boards_to_options(**options)
        except RequestException as e:
            raise forms.ValidationError(
                _('Error adding Trello card: %s') % str(e))

        initial.update({
            'boards': boards,
        })
        return initial

    def get_issue_label(self, group, issue_id, **kwargs):
        iid, iurl = issue_id.split('/', 1)
        return 'Trello-%s' % iid

    def get_issue_url(self, group, issue_id, **kwargs):
        iid, iurl = issue_id.split('/', 1)
        return iurl

    def get_new_issue_title(self, **kwargs):
        return _('Create Trello Card')

    def create_issue(self, request, group, form_data, **kwargs):
        trello = self.get_client(group.project)
        try:
            card = trello.new_card(
                name=form_data['title'],
                desc=form_data['description'],
                idList=form_data['trello_list'],
            )
        except RequestException as e:
            raise forms.ValidationError(
                _('Error adding Trello card: %s') % str(e))

        return '%s/%s' % (card['id'], card['url'])

    def validate_config_field(self, project, name, value, actor=None):
        value = super(TrelloPlugin, self).validate_config_field(project, name, value, actor)
        return value

    def validate_config(self, project, config, actor=None):
        try:
            TrelloClient(config['key'], config['token']).organizations_to_options()
        except RequestException as e:
            raise PluginError('dang')
        return config

    def get_configure_plugin_fields(self, request, project, **kwargs):
        """
            key = forms.CharField(label=_('Trello API Key'))
    token = forms.CharField(label=_('Trello API Token'))
    organization = forms.CharField(label=_('Organization to add a card to'),
                                   max_length=50, required=False)
                                   """
        key = self.get_option('key', project)
        token = self.get_option('token', project)

        organizations = []

        if key and token:
            client = TrelloClient(key, token)
            try:
                organizations = EMPTY + client.organizations_to_options()
            except RequestException:
                pass

        return [{
            'name': 'key',
            'label': 'Trello API Key',
            'type': 'text',
            'default': key,
            'required': True,
        }, {
            'name': 'token',
            'label': 'Trello API Token',
            'type': 'text',
            'default': token,
            'required': True,
        # }, {
        #     'name': 'organization',
        #     'label': 'Organization to add a card to',
        #     # 'max_length': 50,
        #     'type': 'select',
        #     'choices': organizations,
        #     'required': False,
        # }]
        }]
