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
        'sentry_plugins.asana',
        'sentry_plugins.bitbucket',
        'sentry_plugins.heroku',
        'sentry_plugins.hipchat_ac',
        'sentry_plugins.github',
        'sentry_plugins.gitlab',
        'sentry_plugins.pagerduty',
        'sentry_plugins.pivotal',
        'sentry_plugins.pushover',
        'sentry_plugins.jira',
        'sentry_plugins.segment',
        'sentry_plugins.sessionstack',
        'sentry_plugins.slack',
        'sentry_plugins.victorops',
    )

    # TODO(dcramer): we need a PluginAPITestCase that can do register/unregister
    from sentry.plugins import plugins
    from sentry_plugins.asana.plugin import AsanaPlugin
    from sentry_plugins.bitbucket.plugin import BitbucketPlugin
    from sentry_plugins.github.plugin import GitHubPlugin
    from sentry_plugins.gitlab.plugin import GitLabPlugin
    from sentry_plugins.heroku.plugin import HerokuPlugin
    from sentry_plugins.hipchat_ac.plugin import HipchatPlugin
    from sentry_plugins.jira.plugin import JiraPlugin
    from sentry_plugins.pagerduty.plugin import PagerDutyPlugin
    from sentry_plugins.pivotal.plugin import PivotalPlugin
    from sentry_plugins.pushover.plugin import PushoverPlugin
    from sentry_plugins.segment.plugin import SegmentPlugin
    from sentry_plugins.sessionstack.plugin import SessionStackPlugin
    from sentry_plugins.slack.plugin import SlackPlugin
    from sentry_plugins.victorops.plugin import VictorOpsPlugin
    plugins.register(AsanaPlugin)
    plugins.register(BitbucketPlugin)
    plugins.register(GitHubPlugin)
    plugins.register(GitLabPlugin)
    plugins.register(HerokuPlugin)
    plugins.register(HipchatPlugin)
    plugins.register(JiraPlugin)
    plugins.register(PagerDutyPlugin)
    plugins.register(PivotalPlugin)
    plugins.register(PushoverPlugin)
    plugins.register(SegmentPlugin)
    plugins.register(SessionStackPlugin)
    plugins.register(SlackPlugin)
    plugins.register(VictorOpsPlugin)

    settings.ASANA_CLIENT_ID = 'abc'
    settings.ASANA_CLIENT_SECRET = '123'
    settings.BITBUCKET_CONSUMER_KEY = 'abc'
    settings.BITBUCKET_CONSUMER_SECRET = '123'
    settings.GITHUB_APP_ID = 'abc'
    settings.GITHUB_API_SECRET = '123'
