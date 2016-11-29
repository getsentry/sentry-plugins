from __future__ import absolute_import

from django.conf.urls import patterns, url

from .endpoints.webhook import GithubWebhookEndpoint

urlpatterns = patterns(
    '',
    url(r'^organizations/(?P<organization_id>[^\/]+)/webhook/$', GithubWebhookEndpoint.as_view()),
)
