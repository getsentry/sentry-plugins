from __future__ import absolute_import

from django.conf import settings

# Run tests against sqlite for simplicity
import os

os.environ.setdefault('DB', 'sqlite')

pytest_plugins = ['sentry.utils.pytest']


def pytest_configure(config):
    settings.INSTALLED_APPS = tuple(settings.INSTALLED_APPS) + (
        'sentry_plugins.hipchat_ac',
        'sentry_plugins.github',
        'sentry_plugins.pivotal',
    )

    # TODO(dcramer): we need a PluginAPITestCase that can do register/unregister
    from sentry.plugins import plugins
    from sentry_plugins.github.plugin import GitHubPlugin
    from sentry_plugins.hipchat_ac.plugin import HipchatPlugin
    from sentry_plugins.pivotal.plugin import PivotalPlugin
    plugins.register(HipchatPlugin)
    plugins.register(GitHubPlugin)
    plugins.register(PivotalPlugin)
