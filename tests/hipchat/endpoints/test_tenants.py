from __future__ import absolute_import

import six
from django.core.urlresolvers import reverse
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

    def test_start(self):
        user = self.create_user()
        organization = self.create_organization(owner=user)
        team = self.create_team(organization=organization, members=[user])
        project = self.create_project(teams=[team])
        self.create_tenant(auth_user=user, projects=[project])

        self.login_as(user=user)
        response = self.client.get(reverse('sentry-hipchat-ac-start', kwargs={
            'organization_slug': organization.slug,
            'project_slug': project.slug,
        }))

        assert response.status_code == 302
        assert'https://www.hipchat.com/addons/install?url=' in response.url
