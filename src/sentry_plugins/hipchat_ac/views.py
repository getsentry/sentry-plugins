from __future__ import absolute_import

import json
import re
import requests
import six

from functools import update_wrapper
from django import forms
from django.conf import settings
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from sentry import options
from sentry.models import (
    Organization, Team, User, OrganizationMember, GroupAssignee
)
from sentry.utils.http import absolute_uri
from sentry.plugins import plugins
from sentry.web.frontend.base import ProjectView

from .utils import JsonResponse, IS_DEBUG
from .models import Tenant, Context
from . import mentions
from .plugin import (
    enable_plugin_for_tenant, disable_plugin_for_tenant, get_addon_host_ident
)
from .cards import (
    make_event_notification, make_generic_notification,
    make_subscription_update_notification, ICON, ICON2X
)

_regexp_cache = {}

HIPCHAT_ORG_PREFERENCE = 'hipchat_org'
HIPCHAT_PROJECT_PREFERENCE = 'hipchat_project'

REQUIRED_SCOPE = 'project:write'


def get_link_pattern():
    return re.escape(options.get('system.url-prefix')) \
        .replace('https\\:', 'https?\\:') + '/'


def get_link_regexp():
    pattern = get_link_pattern()
    if pattern not in _regexp_cache:
        _regexp_cache[pattern] = re.compile(pattern +
            r'(?P<org>[^/]+)/(?P<proj>[^/]+)/group/'
            r'(?P<group>[^/]+)(/events/(?P<event>[^/]+)|/?)')
    return _regexp_cache[pattern]


def get_addon_key():
    key = getattr(settings, 'HIPCHAT_SENTRY_AC_KEY', None)
    if key is None:
        ident = get_addon_host_ident()
        key = '.'.join(ident.split('.')[::-1]) + '.hipchat-ac'
    return key


class InstallRedirectView(ProjectView):
    required_scope = REQUIRED_SCOPE

    def handle(self, request, organization, team, project):
        # store project and org in session
        # redirect user to hipchat page
        request.session[HIPCHAT_ORG_PREFERENCE] = organization.id
        request.session[HIPCHAT_PROJECT_PREFERENCE] = project.id
        plugin = plugins.get('hipchat-ac')
        return HttpResponseRedirect(plugin.get_install_url())


class DescriptorView(View):

    def get(self, request):
        return JsonResponse({
            'key': get_addon_key(),
            'name': 'Sentry for HipChat',
            'description': 'Sentry integration for HipChat.',
            'links': {
                'self': absolute_uri(reverse('sentry-hipchat-ac-descriptor')),
            },
            'icon': {
                'url': ICON,
            },
            'capabilities': {
                'installable': {
                    'allowRoom': True,
                    'allowGlobal': False,
                    'callbackUrl': absolute_uri(reverse(
                        'sentry-hipchat-ac-installable')),
                },
                'hipchatApiConsumer': {
                    'scopes': ['send_notification', 'view_room'],
                },
                'configurable': {
                    'url': absolute_uri(reverse('sentry-hipchat-ac-config')),
                },
                'webhook': [
                    {
                        'event': 'room_message',
                        'url': absolute_uri(reverse(
                            'sentry-hipchat-ac-link-message')),
                        'pattern': get_link_pattern(),
                        'authentication': 'jwt',
                    },
                ],
                'webPanel': [
                    {
                        'key': 'sentry.sidebar.event-details',
                        'name': {
                            'value': 'Sentry Issue Details',
                        },
                        'location': 'hipchat.sidebar.right',
                        'url': absolute_uri(reverse(
                            'sentry-hipchat-ac-event-details')),
                    },
                    {
                        'key': 'sentry.sidebar.recent-events',
                        'name': {
                            'value': 'Recent Sentry Issues',
                        },
                        'location': 'hipchat.sidebar.right',
                        'url': absolute_uri(reverse(
                            'sentry-hipchat-ac-recent-events')),
                    },
                ],
                'action': [
                    {
                        'key': 'message.sentry.event-details',
                        'name': {
                            'value': 'Show details',
                        },
                        'target': 'sentry-event-details-glance',
                        'location': 'hipchat.message.action',
                        'conditions': [
                            {
                                'condition': 'card_matches',
                                'params': {
                                    'metadata': [
                                        {'attr': 'sentry_message_type',
                                         'eq': 'event'},
                                    ]
                                }
                            }
                        ],
                    },
                    {
                        'key': 'message.sentry.assign-event',
                        'name': {
                            'value': 'Assign',
                        },
                        'target': 'sentry-assign-dialog',
                        'location': 'hipchat.message.action',
                        'conditions': [
                            {
                                'condition': 'card_matches',
                                'params': {
                                    'metadata': [
                                        {'attr': 'sentry_message_type',
                                         'eq': 'event'},
                                    ]
                                }
                            }
                        ],
                    }
                ],
                'dialog': [
                    {
                        'key': 'sentry-assign-dialog',
                        'title': {
                            'value': 'Assign Issue',
                        },
                        'url': absolute_uri(reverse(
                            'sentry-hipchat-assign-event')),
                        'options': {
                            'size': {
                                'height': '400px',
                                'width': '600px',
                            },
                        },
                    }
                ],
                'glance': [
                    # Invisible dummy glance for normal sidebars
                    {
                        'name': {
                            'value': 'Sentry Issue Details',
                        },
                        'key': 'sentry-event-details-glance',
                        'target': 'sentry.sidebar.event-details',
                        'icon': {
                            'url': ICON,
                            'url@2x': ICON2X,
                        },
                        'conditions': [
                            {
                                'condition': 'glance_matches',
                                "params": {
                                    "metadata": [
                                        {"attr": "this_is_a_dummy",
                                         "eq": True}
                                    ]
                                }
                            }
                        ],
                    },
                    {
                        'name': {
                            'value': 'Sentry',
                        },
                        'queryUrl': absolute_uri(reverse(
                            'sentry-hipchat-ac-recent-events-glance')),
                        'key': 'sentry-recent-events-glance',
                        'target': 'sentry.sidebar.recent-events',
                        'icon': {
                            'url': ICON,
                            'url@2x': ICON2X,
                        },
                        'conditions': [],
                    }
                ],
            },
            'vendor': {
                'url': 'https://www.getsentry.com/',
                'name': 'Sentry',
            }
        })


class InstallableView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return View.dispatch(self, *args, **kwargs)

    def post(self, request):
        data = json.loads(request.body) or {}

        room_id = data.get('roomId', None)
        if room_id is None:
            return HttpResponse('This add-on can only be installed in '
                                'individual rooms.', status=400)

        capdoc = requests.get(data['capabilitiesUrl'], timeout=10).json()
        if capdoc['links'].get('self') != data['capabilitiesUrl']:
            return HttpResponse('Mismatch on capabilities URL',
                                status=400)

        try:
            tenant = Tenant.objects.get(pk=data['oauthId'])
            tenant.update_room_info()
        except Tenant.DoesNotExist:
            tenant = Tenant.objects.create(
                id=data['oauthId'],
                room_id=room_id,
                secret=data['oauthSecret'],
                capdoc=capdoc,
            )
            tenant.update_room_info()

        return HttpResponse('', status=201)

    def delete(self, request, oauth_id):
        try:
            tenant = Tenant.objects.get(pk=oauth_id)
            tenant.delete()
        except Tenant.DoesNotExist:
            pass
        return HttpResponse('', status=201)


class GrantAccessForm(forms.Form):
    orgs = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                     label='Organizations',
                                     required=False)

    def __init__(self, tenant, request, initial=None):
        self.user = request.user
        self.tenant = tenant
        self.all_orgs = Organization.objects.get_for_user(request.user, scope=REQUIRED_SCOPE)
        org_choices = [(six.text_type(x.id), x.name) for x in self.all_orgs]
        if request.method == 'POST':
            forms.Form.__init__(self, request.POST)
        else:
            forms.Form.__init__(self, initial)
        self.fields['orgs'].choices = org_choices

    def clean_orgs(self):
        rv = [org for org in self.all_orgs if six.text_type(org.id) in
              self.cleaned_data['orgs']]
        if not rv:
            raise forms.ValidationError('You need to select at least one '
                                        'organization to give access to.')
        return rv

    def save_changes(self):
        self.tenant.auth_user = self.user
        self.tenant.organizations = self.cleaned_data['orgs']
        self.tenant.save()
        notify_tenant_added(self.tenant)


class ProjectSelectForm(forms.Form):
    projects = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                         label='Projects', required=False)

    def __init__(self, tenant, request, initial=None):
        self.tenant = tenant
        project_choices = []
        self.projects_by_id = {}

        for org in tenant.organizations.all():
            teams = Team.objects.get_for_user(org, tenant.auth_user,
                                              scope=REQUIRED_SCOPE,
                                              with_projects=True)
            for team, projects in teams:
                for project in projects:
                    project_choices.append((six.text_type(project.id), '%s | %s / %s' % (
                        org.name, team.name, project.name)))
                    self.projects_by_id[six.text_type(project.id)] = project

        project_choices.sort(key=lambda x: x[1].lower())

        if request.method == 'POST':
            forms.Form.__init__(self, request.POST, initial)
        else:
            forms.Form.__init__(self, initial)

        self.fields['projects'].choices = project_choices

    def clean_projects(self):
        return set(self.cleaned_data['projects'])

    def save_changes(self):
        new_projects = []
        removed_projects = []

        for project_id, project in six.iteritems(self.projects_by_id):
            if project_id in self.cleaned_data['projects']:
                if enable_plugin_for_tenant(project, self.tenant):
                    new_projects.append(project)
            else:
                if disable_plugin_for_tenant(project, self.tenant):
                    removed_projects.append(project)

        if new_projects or removed_projects:
            with Context.for_tenant(self.tenant) as ctx:
                ctx.send_notification(**make_subscription_update_notification(
                    new_projects, removed_projects))
                if removed_projects:
                    mentions.clear_project_mentions(
                        self.tenant, removed_projects)
                ctx.push_recent_events_glance()


def webhook(f):
    @csrf_exempt
    def new_f(request, *args, **kwargs):
        data = json.loads(request.body) or {}
        with Context.for_request(request, data) as context:
            return f(request, context, data, *args, **kwargs)
    return update_wrapper(new_f, f)


def with_context(f):
    def new_f(request, *args, **kwargs):
        with Context.for_request(request) as context:
            return f(request, context, *args, **kwargs)
    return update_wrapper(new_f, f)


def allow_frame(f):
    def new_f(request, *args, **kwargs):
        resp = f(request, *args, **kwargs)
        # put something here so that sentry does not overwrite it
        # with deny.
        resp['X-Frame-Options'] = 'allow'
        return resp
    return update_wrapper(new_f, f)


def cors(f):
    def new_f(request, *args, **kwargs):
        origin = request.META.get('HTTP_ORIGIN')
        resp = f(request, *args, **kwargs)
        resp['Access-Control-Allow-Origin'] = origin
        resp['Access-Control-Request-Method'] = 'GET, HEAD, OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'X-Requested-With'
        resp['Access-Control-Allow-Credentials'] = 'true'
        resp['Access-Control-Max-Age'] = '1728000'
        return resp
    return update_wrapper(new_f, f)


@allow_frame
@with_context
def configure(request, context):
    grant_form = None
    project_select_form = None
    tenant = context.tenant

    project_fields = []
    projects_by_id = {}

    initial_org = None
    initial_project = None

    orgs = [six.text_type(x.id) for x in tenant.organizations.all()]
    org = request.session.get(HIPCHAT_ORG_PREFERENCE, None)

    project = request.session.get(HIPCHAT_PROJECT_PREFERENCE, None)
    if org and org not in set(orgs):
        orgs.append(org)
    initial_org = {
        'orgs': orgs,
    }
    projects = [six.text_type(x.id) for x in tenant.projects.all()]

    if project and project not in set(projects):
        projects.append(project)
    initial_project = {
        'projects': projects
    }

    if context.tenant.auth_user is None and request.user.is_authenticated():
        grant_form = GrantAccessForm(context.tenant, request, initial=initial_org)
        request.session.pop(HIPCHAT_ORG_PREFERENCE, None)
        if request.method == 'POST' and grant_form.is_valid():
            grant_form.save_changes()
            return HttpResponseRedirect(request.get_full_path())

    elif context.tenant.auth_user is not None:
        project_select_form = ProjectSelectForm(context.tenant, request, initial=initial_project or None)
        request.session.pop(HIPCHAT_PROJECT_PREFERENCE, None)
        projects_by_id = project_select_form.projects_by_id
        project_fields = [(f, projects_by_id[f.choice_value]) for f in project_select_form['projects']]
        if request.method == 'POST' and project_select_form.is_valid():
            project_select_form.save_changes()
            messages.add_message(request, messages.SUCCESS, 'Changes saved')
            return HttpResponseRedirect(request.get_full_path())

    return render(request, 'sentry_hipchat_ac/configure.html', {
        'context': context,
        'tenant': context.tenant,
        'current_user': request.user,
        'grant_form': grant_form,
        'project_select_form': project_select_form,
        'available_orgs': list(context.tenant.organizations.all()),
        'hipchat_debug': IS_DEBUG,
        'project_fields': project_fields,
    })


@allow_frame
@with_context
def back(request, context):
    tenant = context.tenant
    tenant.auth_user = None
    tenant.save()
    cfg_url = '%s?signed_request=%s' % (
        reverse('sentry-hipchat-ac-config'),
        context.signed_request
    )
    return HttpResponseRedirect(cfg_url)


@allow_frame
@with_context
def sign_out(request, context):
    tenant = context.tenant
    cfg_url = '%s?signed_request=%s' % (
        reverse('sentry-hipchat-ac-config'),
        context.signed_request
    )

    if 'no' in request.POST:
        return HttpResponseRedirect(cfg_url)
    elif request.method == 'POST':
        if tenant.auth_user:
            tenant.clear()
            notify_tenant_removal(tenant)
        url = "%s?next=%s" % (reverse('sentry-logout'), cfg_url)
        return HttpResponseRedirect(url)

    return render(request, 'sentry_hipchat_ac/sign_out.html', {
        'context': context,
        'tenant': tenant,
    })


@cors
@allow_frame
@with_context
def recent_events_glance(request, context):
    return JsonResponse(context.get_recent_events_glance())


@allow_frame
@with_context
def event_details(request, context):
    event = None
    group = None
    interface_data = {}
    tags = []
    event_id = request.GET.get('event')
    bad_event = False

    if event_id is not None:
        event = context.get_event(event_id)
        if event is None:
            bad_event = True
        else:
            group = event.group

            tags = [(k.split(':', 1)[1] if k.startswith('sentry:') else k,
                     v) for k, v in event.get_tags()]

            interface_data.update(
                http=event.interfaces.get('sentry.interfaces.Http'),
                user=event.interfaces.get('sentry.interfaces.User'),
            )
            exc = event.interfaces.get('sentry.interfaces.Exception')
            if exc is not None:
                interface_data['exc'] = exc
                interface_data['exc_as_string'] = exc.to_string(event)

    return render(request, 'sentry_hipchat_ac/event_details.html', {
        'context': context,
        'event': event,
        'from_recent': request.GET.get('from_recent') == 'yes',
        'group': group,
        'interfaces': interface_data,
        'bad_event': bad_event,
        'tags': tags,
    })


@allow_frame
@with_context
def assign_event(request, context):
    event = None
    project = None
    member_list = []
    assigned_to = None
    dismiss_dialog = False

    event_id = request.GET.get('event')
    if event_id:
        event = context.get_event(event_id)
        if event is not None:
            project = event.project
            member_list = sorted(set(User.objects.filter(
                is_active=True,
                sentry_orgmember_set__organization=project.organization,
                sentry_orgmember_set__id__in=OrganizationMember.objects.filter(
                    organizationmemberteam__is_active=True,
                    organizationmemberteam__team=project.team,
                ).values('id')
            ).distinct()[:1000]), key=lambda x: x.email)
            assigned_to = GroupAssignee.objects.filter(
                group=event.group
            ).first()

            if request.method == 'POST':
                if 'assign' in request.POST:
                    assignee = next((
                        x for x in member_list
                        if six.text_type(x.id) == request.POST['assigned_to']), None)
                    if assignee is not None:
                        GroupAssignee.objects.assign(event.group, assignee)
                elif 'deassign' in request.POST:
                    GroupAssignee.objects.deassign(event.group)
                dismiss_dialog = True

    return render(request, 'sentry_hipchat_ac/assign_event.html', {
        'context': context,
        'event': event,
        'project': project,
        'member_list': member_list,
        'assigned_to': assigned_to,
        'dismiss_dialog': dismiss_dialog,
    })


@allow_frame
@with_context
def recent_events(request, context):
    events = mentions.get_recent_mentions(context.tenant)
    return render(request, 'sentry_hipchat_ac/recent_events.html', {
        'context': context,
        'events': events,
    })


@webhook
def on_link_message(request, context, data):
    match = get_link_regexp().search(data['item']['message']['message'])
    if match is not None:
        params = match.groupdict()
        event = context.get_event_from_url_params(
            group_id=params['group'],
            event_id=params['event'],
            slug_vars={'org_slug': params['org'],
                       'proj_slug': params['proj']}
        )
        if event is not None:
            context.send_notification(**make_event_notification(
                event.group, event, context.tenant, new=False,
                event_target=params['event'] is not None))

            mentions.mention_event(
                project=event.project,
                group=event.group,
                tenant=context.tenant,
                event=params['event'] and event or None,
            )
            context.push_recent_events_glance()

    return HttpResponse('', status=204)


def notify_tenant_added(tenant):
    with Context.for_tenant(tenant) as ctx:
        ctx.send_notification(**make_generic_notification(
            'The Sentry Hipchat integration was associated with this room.',
            color='green'))
        ctx.push_recent_events_glance()


def notify_tenant_removal(tenant):
    with Context.for_tenant(tenant) as ctx:
        ctx.send_notification(**make_generic_notification(
            'The Sentry Hipchat integration was disassociated with this room.',
            color='red'))
        ctx.push_recent_events_glance()
