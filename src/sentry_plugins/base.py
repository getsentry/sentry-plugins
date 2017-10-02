from __future__ import absolute_import

import pkg_resources
import sentry_plugins
import six

from sentry.exceptions import InvalidIdentity, PluginError

from sentry_plugins.constants import ERR_INTERNAL, ERR_UNAUTHORIZED, ERR_UNSUPPORTED_RESPONSE_TYPE
from sentry_plugins.exceptions import ApiError, ApiHostError, ApiUnauthorized, UnsupportedResponseType


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

    # TODO(dcramer): The following is a possible "better implementation" of the
    # core issue implementation, though it would need a compat layer to push
    # it upstream
    def error_message_from_json(self, data):
        return data.get('message', 'unknown error')

    def message_from_error(self, exc):
        if isinstance(exc, ApiUnauthorized):
            return ERR_UNAUTHORIZED
        elif isinstance(exc, ApiHostError):
            return exc.text
        elif isinstance(exc, UnsupportedResponseType):
            return ERR_UNSUPPORTED_RESPONSE_TYPE.format(
                content_type=exc.content_type,
            )
        elif isinstance(exc, ApiError):
            if exc.json:
                msg = self.error_message_from_json(exc.json) or 'unknown error'
            else:
                msg = 'unknown error'
            return (
                'Error Communicating with %s (HTTP %s): %s' % (
                    self.title,
                    exc.code,
                    msg
                )
            )
        else:
            return ERR_INTERNAL

    def raise_error(self, exc):
        if isinstance(exc, ApiUnauthorized):
            raise InvalidIdentity(self.message_from_error(exc))
        elif isinstance(exc, ApiError):
            raise PluginError(self.message_from_error(exc))
        elif isinstance(exc, PluginError):
            raise
        else:
            self.logger.exception(six.text_type(exc))
            raise PluginError(self.message_from_error(exc))


def assert_package_not_installed(name):
    try:
        pkg_resources.get_distribution(name)
    except pkg_resources.DistributionNotFound:
        return
    else:
        raise RuntimeError(
            "Found %r. This has been superseded by 'sentry-plugins', so please uninstall." % name
        )
