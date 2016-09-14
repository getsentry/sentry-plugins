from __future__ import absolute_import

from sentry.plugins import Plugin

import sentry_plugins


class JiraACPlugin(Plugin):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry/sentry-plugins'
    version = sentry_plugins.VERSION
    description = "Add a Sentry UI Plugin to JIRA"
    resource_links = [
        ('Bug Tracker', 'https://github.com/getsentry/sentry-plugins/issues'),
        ('Source', 'https://github.com/getsentry/sentry-plugins'),
    ]

    slug = 'jira-ac'
    title = 'JIRA Atlassian Connect'
    conf_title = title
    conf_key = 'jira-ac'

    def get_url_module(self):
        return 'sentry_plugins.jira_ac.urls'
