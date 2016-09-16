from __future__ import absolute_import

import sentry_plugins


class CorePluginMixin(object):
    author = 'Sentry Team'
    author_url = 'https://github.com/getsentry/sentry-plugins'
    version = sentry_plugins.VERSION
    resource_links = [
        ('Bug Tracker', 'https://github.com/getsentry/sentry-plugins/issues'),
        ('Source', 'https://github.com/getsentry/sentry-plugins'),
    ]

    # HACK(dcramer): work around MRO issue with plugin metaclass
    logger = None
