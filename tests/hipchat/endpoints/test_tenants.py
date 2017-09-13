from __future__ import absolute_import

import six

from sentry.testutils import APITestCase

from sentry_plugins.hipchat_ac.testutils import HipchatFixture


class HipchatTenantsTest(APITestCase, HipchatFixture):
    def test_simple(self):
        project = self.project  # force creation

        url = '/api/0/projects/{}/{}/plugins/hipchat-ac/tenants/'.format(
            project.organization.slug,
            project.slug,
        )

        tenant1 = self.create_tenant(
            auth_user=self.user,
            projects=[project],
        )
        tenant2 = self.create_tenant(
            auth_user=None,
            projects=[project],
        )

        self.login_as(user=self.user)

        response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == tenant1.id
        assert response.data[0]['authUser']['id'] == six.text_type(self.user.id)
        assert response.data[1]['id'] == tenant2.id
        assert response.data[1]['authUser'] is None
