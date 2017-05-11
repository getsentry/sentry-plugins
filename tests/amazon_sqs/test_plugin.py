from __future__ import absolute_import

from exam import fixture
from mock import patch
from sentry.testutils import PluginTestCase
from sentry.utils import json

from sentry_plugins.amazon_sqs.plugin import AmazonSQSPlugin


class AmazonSQSPluginTest(PluginTestCase):
    @fixture
    def plugin(self):
        return AmazonSQSPlugin()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'amazon-sqs'

    def test_entry_point(self):
        self.assertAppInstalled('amazon_sqs', 'sentry_plugins.amazon_sqs')
        self.assertPluginInstalled('amazon_sqs', self.plugin)

    @patch('boto3.client')
    def test_simple_notification(self, mock_client):
        self.plugin.set_option('access_key', 'access-key', self.project)
        self.plugin.set_option('secret_key', 'secret-key', self.project)
        self.plugin.set_option('region', 'us-east-1', self.project)
        self.plugin.set_option('queue_url', 'https://sqs-us-east-1.amazonaws.com/12345678/myqueue', self.project)

        group = self.create_group(message='Hello world', culprit='foo.bar')
        event = self.create_event(
            group=group,
            data={
                'sentry.interfaces.Exception': {
                    'type': 'ValueError',
                    'value': 'foo bar',
                },
                'sentry.interfaces.User': {
                    'id': '1',
                    'email': 'foo@example.com',
                },
                'type': 'error',
                'metadata': {
                    'type': 'ValueError',
                    'value': 'foo bar',
                },
            },
            tags={'level': 'warning'},
        )

        with self.options({'system.url-prefix': 'http://example.com'}):
            self.plugin.post_process(event)

        mock_client.assert_called_once_with(
            service_name='sqs',
            region_name='us-east-1',
            aws_access_key_id='access-key',
            aws_secret_access_key='secret-key',
        )
        mock_client.return_value.send_message.assert_called_once_with(
            QueueUrl='https://sqs-us-east-1.amazonaws.com/12345678/myqueue',
            MessageBody=json.dumps(self.plugin.get_event_payload(event)),
        )
