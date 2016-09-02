from __future__ import absolute_import

from sentry.testutils import APITestCase

from sentry_plugins.hipchat_ac.models import Tenant


CAPDOC_EXAMPLE = {
    'vendor': {
        'url': 'http://atlassian.com',
        'name': 'Atlassian',
    },
    'name': 'HipChat',
    'links': {
        'self': 'https://api.hipchat.com/v2/capabilities',
        'api': 'https://api.hipchat.com/v2',
        'homepage': 'https://www.hipchat.com',
        'subdomain': 'https://www.hipchat.com',
    },
    'capabilities': {
        'oauth2Provider': {
            'tokenUrl': 'https://api.hipchat.com/v2/oauth/token',
            'authorizationUrl': 'https://www.hipchat.com/users/authorize',
        },
        'hipchatApiProvider': {
            'url': 'https://api.hipchat.com/v2/',
            'availableScopes': {
                'admin_room': {
                    'description': 'Perform room administrative tasks',
                    'name': 'Administer Room',
                    'id': 'admin_room',
                },
                'manage_rooms': {
                    'description': 'Create, update, and remove rooms',
                    'name': 'Manage Rooms',
                    'id': 'manage_rooms'
                },
                'import_data': {
                    'description': 'Import users, rooms, and chat history. Only available for select add-ons.',
                    'name': 'Import Data',
                    'id': 'import_data',
                },
                'view_room': {
                    'description': 'View room information and participants, but not history',
                    'name': 'View Room',
                    'id': 'view_room',
                },
                'send_message': {
                    'description': 'Send private one-on-one messages',
                    'name': 'Send Message',
                    'id': 'send_message',
                },
                'view_messages': {
                    'description': 'View messages from chat rooms and private chats you have access to',
                    'name': 'View Messages',
                    'id': 'view_messages'
                },
                'admin_group': {
                    'description': "Perform group administrative tasks. Note that this scope is restricted from updating the group owner's profile.",
                    'name': 'Administer Group',
                    'id': 'admin_group',
                },
                'send_notification': {
                    'description': 'Send room notifications',
                    'name': 'Send Notification',
                    'id': 'send_notification',
                },
                'view_group': {
                    'description': 'View users, rooms, and other group information',
                    'name': 'View Group',
                    'id': 'view_group',
                },
            },
        },
    },
    'connect_server_api_version': 1,
    'key': 'hipchat',
    'description': 'Group chat and IM built for teams',
}


class HipchatTenantsTest(APITestCase):
    def test_simple(self):
        project = self.project  # force creation

        url = '/api/0/projects/{}/{}/plugins/hipchat-ac/tenants/'.format(
            project.organization.slug,
            project.slug,
        )

        tenant = Tenant.objects.create(
            id='1',
            room_id='2',
            secret='top secret',
            capdoc=CAPDOC_EXAMPLE,
        )
        tenant.update(auth_user=self.user)
        tenant.projects.add(project)
        tenant.organizations.add(project.organization)

        self.login_as(user=self.user)

        response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == tenant.id
