from __future__ import absolute_import

import six

from sentry.plugins.endpoints import PluginProjectEndpoint


class HipchatTenantsEndpoint(PluginProjectEndpoint):
    def get(self, request, project, *args, **kwargs):
        queryset = project.hipchat_tenant_set.select_related('auth_user')

        return self.respond([{
            'id': t.id,
            'room': {
                'id': t.room_id,
                'name': t.room_name,
                'owner': {
                    'id': t.room_owner_id,
                    'name': t.room_owner_name,
                },
                'homepage': t.homepage,
            },
            'authUser': {
                'id': six.text_type(t.auth_user.id),
                'name': t.auth_user.get_display_name(),
                'username': t.auth_user.username,
                'email': t.auth_user.email,
            } if t.auth_user else None,
        } for t in queryset])
