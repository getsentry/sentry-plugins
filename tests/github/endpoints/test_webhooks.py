# -*- coding: utf-8 -*-
from __future__ import absolute_import

import six

from datetime import datetime
from django.utils import timezone
from sentry.models import Commit, OrganizationOption, Repository
from sentry.testutils import APITestCase
from uuid import uuid4

from sentry_plugins.github.testutils import PUSH_EVENT_EXAMPLE


class WebhookTest(APITestCase):
    def test_get(self):
        project = self.project  # force creation

        url = '/plugins/github/organizations/{}/webhook/'.format(
            project.organization.id,
        )

        response = self.client.get(url)

        assert response.status_code == 405

    def test_unregistered_event(self):
        project = self.project  # force creation

        url = '/plugins/github/organizations/{}/webhook/'.format(
            project.organization.id,
        )

        secret = 'b3002c3e321d4b7880360d397db2ccfd'

        OrganizationOption.objects.set_value(
            organization=project.organization,
            key='github:webhook_secret',
            value=secret,
        )

        response = self.client.post(
            path=url,
            data=PUSH_EVENT_EXAMPLE,
            content_type='application/json',
            HTTP_X_GITHUB_EVENT='UnregisteredEvent',
            HTTP_X_HUB_SIGNATURE='sha1=df94a49a15c8235a6e5890376b67f853e3e9d3a8',
            HTTP_X_GITHUB_DELIVERY=six.text_type(uuid4())
        )

        assert response.status_code == 204

    def test_invalid_signature_event(self):
        project = self.project  # force creation

        url = '/plugins/github/organizations/{}/webhook/'.format(
            project.organization.id,
        )

        secret = '2d7565c3537847b789d6995dca8d9f84'

        OrganizationOption.objects.set_value(
            organization=project.organization,
            key='github:webhook_secret',
            value=secret,
        )

        response = self.client.post(
            path=url,
            data=PUSH_EVENT_EXAMPLE,
            content_type='application/json',
            HTTP_X_GITHUB_EVENT='push',
            HTTP_X_HUB_SIGNATURE='sha1=33521abeaaf9a57c2abf486e0ccd54d23cf36fec',
            HTTP_X_GITHUB_DELIVERY=six.text_type(uuid4())
        )

        assert response.status_code == 401


class PushEventWebhookTest(APITestCase):
    def test_simple(self):
        project = self.project  # force creation

        url = '/plugins/github/organizations/{}/webhook/'.format(
            project.organization.id,
        )

        secret = 'b3002c3e321d4b7880360d397db2ccfd'

        OrganizationOption.objects.set_value(
            organization=project.organization,
            key='github:webhook_secret',
            value=secret,
        )

        Repository.objects.create(
            organization_id=project.organization.id,
            external_id='35129377',
            provider='github',
            name='baxterthehacker/public-repo',
        )

        response = self.client.post(
            path=url,
            data=PUSH_EVENT_EXAMPLE,
            content_type='application/json',
            HTTP_X_GITHUB_EVENT='push',
            HTTP_X_HUB_SIGNATURE='sha1=df94a49a15c8235a6e5890376b67f853e3e9d3a8',
            HTTP_X_GITHUB_DELIVERY=six.text_type(uuid4())
        )

        assert response.status_code == 204

        commit_list = list(Commit.objects.filter(
            organization_id=project.organization_id,
        ).select_related('author').order_by('-date_added'))

        assert len(commit_list) == 2

        commit = commit_list[0]

        assert commit.key == '133d60480286590a610a0eb7352ff6e02b9674c4'
        assert commit.message == u'Update README.md (àgain)'
        assert commit.author.name == u'bàxterthehacker'
        assert commit.author.email == 'baxterthehacker@users.noreply.github.com'
        assert commit.date_added == datetime(2015, 5, 5, 23, 45, 15, tzinfo=timezone.utc)

        commit = commit_list[1]

        assert commit.key == '0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c'
        assert commit.message == 'Update README.md'
        assert commit.author.name == u'bàxterthehacker'
        assert commit.author.email == 'baxterthehacker@users.noreply.github.com'
        assert commit.date_added == datetime(2015, 5, 5, 23, 40, 15, tzinfo=timezone.utc)
