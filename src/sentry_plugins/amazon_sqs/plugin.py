from __future__ import absolute_import

import logging

import boto3
from botocore.client import ClientError

from sentry_plugins.base import CorePluginMixin
from sentry.plugins.bases.data_forwarding import DataForwardingPlugin
from sentry_plugins.utils import get_secret_field_config
from sentry.utils import json, metrics

logger = logging.getLogger(__name__)


def get_regions():
    return boto3.session.Session().get_available_regions("sqs")


class AmazonSQSPlugin(CorePluginMixin, DataForwardingPlugin):
    title = "Amazon SQS"
    slug = "amazon-sqs"
    description = "Forward Sentry events to Amazon SQS."
    conf_key = "amazon-sqs"

    def get_config(self, project, **kwargs):
        return [
            {
                "name": "queue_url",
                "label": "Queue URL",
                "type": "url",
                "placeholder": "https://sqs-us-east-1.amazonaws.com/12345678/myqueue",
            },
            {
                "name": "region",
                "label": "Region",
                "type": "select",
                "choices": tuple((z, z) for z in get_regions()),
            },
            get_secret_field_config(
                name="access_key", label="Access Key", secret=self.get_option("access_key", project)
            ),
            get_secret_field_config(
                name="secret_key", label="Secret Key", secret=self.get_option("secret_key", project)
            ),
        ]

    def forward_event(self, event, payload):
        queue_url = self.get_option("queue_url", event.project)
        access_key = self.get_option("access_key", event.project)
        secret_key = self.get_option("secret_key", event.project)
        region = self.get_option("region", event.project)

        if not all((queue_url, access_key, secret_key, region)):
            return

        # TODO(dcramer): Amazon doesnt support payloads larger than 256kb
        # We could support this by simply trimming it and allowing upload
        # to S3
        message = json.dumps(payload)
        if len(message) > 256 * 1024:
            return False

        try:
            client = boto3.client(
                service_name="sqs",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )
            client.send_message(QueueUrl=queue_url, MessageBody=message)
        except ClientError as e:
            if e.message.startswith("An error occurred (AccessDenied)"):
                # If there's an issue with the user's token then we can't do
                # anything to recover. Just log and continue.
                metrics_name = "sentry_plugins.amazon_sqs.access_token_invalid"
                logger.info(
                    metrics_name,
                    extra={
                        "queue_url": queue_url,
                        "access_key": access_key,
                        "region": region,
                        "project_id": event.project.id,
                        "organization_id": event.project.organization_id,
                    },
                )
                metrics.incr(
                    metrics_name,
                    tags={
                        "project_id": event.project_id,
                        "organization_id": event.project.organization_id,
                    },
                )
                return False
            raise

        return True
