from __future__ import absolute_import

from django.conf import settings
from django.core.urlresolvers import reverse
from six.moves.urllib.parse import urlparse, quote

from sentry import options
from sentry.plugins import plugins
from sentry.plugins.bases.notify import NotifyPlugin
from sentry.utils.http import absolute_uri

from sentry_plugins.base import CorePluginMixin

from .cards import make_event_notification, make_activity_notification
from .endpoints.tenants import HipchatTenantsEndpoint
from .endpoints.test_config import HipchatTestConfigEndpoint


COLORS = {
    'ALERT': 'red',
    'ERROR': 'red',
    'WARNING': 'yellow',
    'INFO': 'green',
    'DEBUG': 'purple',
}


def get_addon_host_ident():
    ident = urlparse(options.get('system.url-prefix')).hostname
    if ident in ('localhost', '127.0.0.1', None, ''):
        return 'app.dev.getsentry.com'
    return ident


def is_on_premise():
    return get_addon_host_ident() in ('app.getsentry.com', 'sentry.io')


def enable_plugin_for_tenant(project, tenant):
    rv = False
    plugin = plugins.get('hipchat-ac')

    # Make sure the plugin itself is enabled.
    plugin.enable(project)

    # Add our tenant to the plugin.
    active = set(plugin.get_option('tenants', project) or ())
    if tenant.id not in active:
        active.add(tenant.id)
        tenant.projects.add(project)
        rv = True
    plugin.set_option('tenants', sorted(active), project)

    return rv


def disable_plugin_for_tenant(project, tenant):
    rv = False
    plugin = plugins.get('hipchat-ac')

    # Remove our tenant to the plugin.
    active = set(plugin.get_option('tenants', project) or ())
    if tenant.id in active:
        tenant.projects.remove(project)
        active.discard(tenant.id)
        rv = True
    plugin.set_option('tenants', sorted(active), project)

    # If the last tenant is gone, we disable the entire plugin.
    if not active:
        plugin.disable(project)

    return rv


class HipchatPlugin(CorePluginMixin, NotifyPlugin):
    description = 'Bring Sentry to HipChat.'
    slug = 'hipchat-ac'
    title = 'HipChat'
    conf_title = title
    conf_key = 'hipchat-ac'
    timeout = getattr(settings, 'SENTRY_HIPCHAT_TIMEOUT', 3)

    asset_key = 'hipchat_ac'
    assets = [
        'dist/hipchat-ac.js',
    ]

    def get_descriptor(self):
        return absolute_uri(reverse('sentry-hipchat-ac-descriptor'))

    def get_install_url(self):
        return (
            'https://www.hipchat.com/addons/install?url=' +
            quote(absolute_uri(reverse('sentry-hipchat-ac-descriptor')))
        )

    def get_project_urls(self):
        return [
            (r'^tenants/', HipchatTenantsEndpoint.as_view(plugin=self)),
            (r'^test-config/', HipchatTestConfigEndpoint.as_view(plugin=self)),
        ]

    def get_metadata(self):
        return {
            'descriptor': self.get_descriptor(),
            'installUrl': self.get_install_url(),
            'onPremise': is_on_premise(),
        }

    def get_config(self, project, **kwargs):
        return []

    def is_configured(self, project):
        return bool(self.get_option('tenants', project))

    def get_url_module(self):
        return 'sentry_plugins.hipchat_ac.urls'

    def disable(self, project=None, user=None):
        was_enabled = self.get_option('enabled', project)
        NotifyPlugin.disable(self, project, user)

        if project is not None and was_enabled:
            for tenant in Tenant.objects.filter(projects__in=[project]):
                disable_plugin_for_tenant(project, tenant)

    def notify_users(self, group, event, fail_silently=False):
        tenants = Tenant.objects.filter(projects=event.project)
        for tenant in tenants:
            with Context.for_tenant(tenant) as ctx:
                ctx.send_notification(**make_event_notification(
                    group, event, tenant))

                mentions.mention_event(
                    project=event.project,
                    group=group,
                    tenant=tenant,
                    event=event,
                )
                ctx.push_recent_events_glance()

    def notify_about_activity(self, activity):
        tenants = Tenant.objects.filter(projects=activity.project)
        for tenant in tenants:
            with Context.for_tenant(tenant) as ctx:
                n = make_activity_notification(activity, tenant)
                if n is not None:
                    ctx.send_notification(**n)


from .models import Tenant, Context
from . import mentions
