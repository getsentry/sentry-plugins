from __future__ import absolute_import

import logging

from sentry.exceptions import PluginError

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.constants import ERR_UNAUTHORIZED

from .client import VstsClient


class VisualStudioMixin(CorePluginMixin):
    logger = logging.getLogger('sentry.plugins.visualstudio')
    title = 'Visual Studio'

    def get_client(self, user):
        auth = self.get_auth(user=user)
        if auth is None:
            raise PluginError(ERR_UNAUTHORIZED)
        return VstsClient(auth)
