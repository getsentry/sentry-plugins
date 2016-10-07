from __future__ import absolute_import

from exam import fixture
from sentry.testutils import PluginTestCase

from sentry_plugins.pivotal.plugin import PivotalPlugin


class PivotalPluginTest(PluginTestCase):
    @fixture
    def plugin(self):
        return PivotalPlugin()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'pivotal'

    def test_entry_point(self):
        self.assertAppInstalled('pivotal', 'sentry_plugins.pivotal')
        self.assertPluginInstalled('pivotal', self.plugin)

    def test_get_issue_label(self):
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert self.plugin.get_issue_label(group, 1) == '#1'

    def test_get_issue_url(self):
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert self.plugin.get_issue_url(group, 1) == 'https://www.pivotaltracker.com/story/show/1'

    def test_is_configured(self):
        assert self.plugin.is_configured(None, self.project) is False
        self.plugin.set_option('token', '1', self.project)
        self.plugin.set_option('project', '1', self.project)
        assert self.plugin.is_configured(None, self.project) is True
