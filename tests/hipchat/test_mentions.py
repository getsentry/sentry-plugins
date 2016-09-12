from __future__ import absolute_import

from sentry.testutils import TestCase

from sentry_plugins.hipchat_ac import mentions
from sentry_plugins.hipchat_ac.testutils import HipchatFixture


class HipchatMentionsTest(TestCase, HipchatFixture):
    def test_simple(self):
        project = self.create_project(name='bar')
        project2 = self.create_project(name='foo')
        group = self.create_group(project=project)
        event = self.create_event(group=group)
        tenant = self.create_tenant(projects=[project])

        mentions.mention_event(project, group, tenant, event)

        assert mentions.count_recent_mentions(tenant) == 1

        result = mentions.get_recent_mentions(tenant)

        assert len(result) == 1
        assert result[0]['project'] == project
        assert result[0]['group'] == group
        assert result[0]['event'] == event
        assert result[0]['last_mentioned']

        mentions.clear_project_mentions(tenant, [project2])

        assert mentions.count_recent_mentions(tenant) == 1

        mentions.clear_project_mentions(tenant, [project])

        assert mentions.count_recent_mentions(tenant) == 0

        result = mentions.get_recent_mentions(tenant)

        assert not result

        mentions.mention_event(project, group, tenant, event)
        mentions.clear_tenant_mentions(tenant)

        assert mentions.count_recent_mentions(tenant) == 0

        result = mentions.get_recent_mentions(tenant)

        assert not result
