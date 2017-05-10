from __future__ import absolute_import

from sentry.testutils import PluginTestCase

from sentry_plugins.hipchat_ac import views


class HipchatPluginTest(PluginTestCase):
    def test_link_regex(self):
        match_old = views.get_link_regexp().search(views.options.get('system.url-prefix') + "/org/proj/group/123/events/456")
        assert match_old is not None

        match_new = views.get_link_regexp().search(views.options.get('system.url-prefix') + "/org/proj/issues/123/events/456")
        assert match_new is not None
