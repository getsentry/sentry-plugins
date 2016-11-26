from __future__ import absolute_import

from sentry import http
from sentry.app import ratelimiter
from sentry.plugins.base import Plugin
from sentry.utils.hashlib import md5_text

from sentry_plugins.base import CorePluginMixin


class StripePlugin(CorePluginMixin, Plugin):
    title = 'Stripe'
    slug = 'stripe'
    description = 'Add rich Stripe context to events.'
    conf_key = 'stripe'

    asset_key = 'stripe'
    assets = [
        'dist/stripe.js',
    ]

    def get_config(self, project, **kwargs):
        return [{
            'name': 'key',
            'label': 'Read Key',
            'type': 'secret',
            'required': True,
        }]

    def get_metadata(self):
        return {

        }

    # def get_group_urls(self):
    #     return super(StripePlugin, self).get_group_urls() + [
    #         (r'^autocomplete', IssueGroupActionEndpoint.as_view(
    #             view_method_name='view_autocomplete',
    #             plugin=self,
    #         )),
    #     ]
