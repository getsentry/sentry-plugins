from __future__ import absolute_import

from django.conf import settings

import os
import sys

# Run tests against sqlite for simplicity
os.environ.setdefault('DB', 'sqlite')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

pytest_plugins = ['sentry.utils.pytest']


def pytest_configure(config):
    settings.INSTALLED_APPS = tuple(settings.INSTALLED_APPS) + (
        'sentry_plugins.hipchat_ac',
        'sentry_plugins.github',
        'sentry_plugins.gitlab',
        'sentry_plugins.pivotal',
        'sentry_plugins.teamwork',
    )

    # TODO(dcramer): we need a PluginAPITestCase that can do register/unregister
    from sentry.plugins import plugins
    from sentry_plugins.github.plugin import GitHubPlugin
    from sentry_plugins.gitlab.plugin import GitLabPlugin
    from sentry_plugins.hipchat_ac.plugin import HipchatPlugin
    from sentry_plugins.pivotal.plugin import PivotalPlugin
    from sentry_plugins.teamwork.plugin import TeamworkPlugin
    plugins.register(HipchatPlugin)
    plugins.register(GitHubPlugin)
    plugins.register(GitLabPlugin)
    plugins.register(PivotalPlugin)
    plugins.register(TeamworkPlugin)
