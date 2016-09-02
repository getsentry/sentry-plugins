from __future__ import absolute_import

from exam import fixture
from django.test import RequestFactory
from sentry.testutils import TestCase

from sentry_plugins.hipchat_ac.plugin import HipchatPlugin


class HipchatPluginTest(TestCase):
    @fixture
    def plugin(self):
        return HipchatPlugin()

    @fixture
    def request(self):
        return RequestFactory()

    def test_is_configured(self):
        assert self.plugin.is_configured(self.project) is False
        self.plugin.set_option('tenants', [1], self.project)
        assert self.plugin.is_configured(self.project) is True
