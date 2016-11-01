from __future__ import absolute_import

import pkg_resources
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


def assert_package_not_installed(name):
    try:
        pkg_resources.get_distribution(name)
    except pkg_resources.DistributionNotFound:
        return
    else:
        raise RuntimeError("Found %r. This has been superseded by 'sentry-plugins', so please uninstall." % name)
