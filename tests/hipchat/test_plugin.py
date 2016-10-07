from __future__ import absolute_import

from exam import fixture
from django.test import RequestFactory
from sentry.testutils import PluginTestCase

from sentry_plugins.hipchat_ac.plugin import HipchatPlugin


class HipchatPluginTest(PluginTestCase):
    @fixture
    def plugin(self):
        return HipchatPlugin()

    @fixture
    def request(self):
        return RequestFactory()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'hipchat-ac'

    def test_entry_point(self):
        self.assertAppInstalled('hipchat_ac', 'sentry_plugins.hipchat_ac')
        self.assertPluginInstalled('hipchat_ac', self.plugin)

    def test_is_configured(self):
        assert self.plugin.is_configured(self.project) is False
        self.plugin.set_option('tenants', [1], self.project)
        assert self.plugin.is_configured(self.project) is True
