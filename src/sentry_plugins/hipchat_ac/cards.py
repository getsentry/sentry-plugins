# -*- coding: utf-8 -*-
from __future__ import absolute_import

import six

from django.utils.html import escape

from sentry.models import Activity, User, Event


ICON = 'https://sentry-hipchat-ac-assets.s3.amazonaws.com/sentry-icon.png'
ICON2X = 'https://sentry-hipchat-ac-assets.s3.amazonaws.com/sentry-icon.png'
ICON_SM = 'https://sentry-hipchat-ac-assets.s3.amazonaws.com/favicon.ico'

COLORS = {
    'ALERT': 'red',
    'ERROR': 'red',
    'WARNING': 'yellow',
    'INFO': 'green',
    'DEBUG': 'purple',
}


def _format_user(user):
    if user is None:
        name = 'system'
    elif user.name:
        name = user.name
    else:
        parts = user.username.split('@')
        if len(parts) == 1:
            name = user.username
        else:
            name = parts[0].lower()
    return '<em>%s</em>' % escape(name)


def _make_event_card(group, event, title=None, subtitle=None,
                     event_target=False, new=False, description=None,
                     compact=False):
    project = event.project
    link = group.get_absolute_url()
    if event_target:
        link = '%s/events/%s/' % (
            link.rstrip('/'),
            event.id
        )

    event_title = '%sSentry %s Issue' % (
        new and 'New ' or '',
        group.get_level_display().title(),
    )
    if title is None:
        title = escape(event_title)

    attributes = []
    for key, value in event.tags:
        if key.startswith('sentry:'):
            key = key.split(':', 1)[1]
        attr = {
            'label': key,
            'value': {'label': value}
        }
        if key == 'level':
            attr_color = {
                'critical': 'lozenge-error',
                'fatal': 'lozenge-error',
                'error': 'lozenge-error',
                'warning': 'lozenge-current',
                'debug': 'lozenge-moved',
            }.get(value.lower())
            if attr_color is not None:
                attr['value']['style'] = attr_color
        elif key == 'release':
            attr['value']['style'] = 'lozenge-success'
        attributes.append(attr)

    fold_description = '%s. Issue has been seen %s time%s. First seen %s%s.' % (
        group.get_level_display().title() + ' in Sentry',
        group.times_seen,
        group.times_seen != 1 and 's' or '',
        group.first_seen.strftime('%Y-%m-%d'),
        (group.first_release and ' (%s)' %
            group.first_release.short_version or ''),
    )

    if compact and description is None:
        description = ''

    if description is None:
        description = '<a href="%(link)s"><em>%(err)s</em></a>' % {
            'link': escape(link),
            'err': escape(event.error()),
        }
    if description:
        description = '<p>%s</p>' % description

    extra = ''
    if not compact:
        extra = '''
            <p>
                <strong>Project:</strong>
                <a href="%(project_link)s">%(project)s</a>&nbsp;
                <strong>Culprit:</strong>
                 %(culprit)s
        ''' % {
            'project': escape(project.name),
            'project_link': escape(project.get_absolute_url()),
            'culprit': escape(event.culprit),
        }
    else:
        attributes = [{
            'label': 'culprit',
            'value': {'label': event.culprit},
        }, {
            'label': 'title',
            'value': {'label': event.error()},
        }] + attributes

    return {
        'style': 'application',
        'url': link,
        'id': 'sentry/%s' % event.id,
        'title': event_title,
        'description': fold_description,
        'images': {},
        'icon': {
            'url': ICON,
            'url@2x': ICON2X,
        },
        'metadata': {
            'event': six.text_type(event.id),
            'sentry_message_type': 'event',
        },
        'attributes': attributes,
        'activity': {
            'html': '''
            <p>
            <a href="%(link)s">
                <img src="%(icon_sm)s" style="width: 16px; height: 16px">
                <strong>%(title)s</strong></a>
            %(subtitle)s
            %(description)s
            %(extra)s
            ''' % {
                'title': title,
                'subtitle': subtitle or '',
                'link': escape(link),
                'icon': ICON,
                'icon_sm': ICON_SM,
                'description': description,
                'extra': extra,
            }
        },
    }


def make_event_notification(group, event, tenant, new=True, event_target=False):
    project = event.project
    level = group.get_level_display().upper()

    link = group.get_absolute_url()
    if event_target:
        link = '%s/events/%s/' % (
            link.rstrip('/'),
            event.id
        )

    color = COLORS.get(level, 'purple')

    # Legacy message
    message = (
        '[%(level)s]%(project_name)s %(message)s '
        '[<a href="%(link)s">view</a>]'
    ) % {
        'level': escape(level),
        'project_name': '<strong>%s</strong>' % escape(project.name),
        'message': escape(event.error()),
        'link': escape(link),
    }

    return {
        'color': color,
        'message': message,
        'format': 'html',
        'card': _make_event_card(group, event, new=new,
                                 event_target=event_target),
        'notify': True,
    }


def make_activity_notification(activity, tenant):
    if activity.type in (Activity.UNASSIGNED, Activity.ASSIGNED):
        if activity.type == Activity.ASSIGNED:
            assignee_id = activity.data.get('assignee')
        else:
            assignee_id = None

        if assignee_id is None:
            target_user = None
        else:
            target_user = User.objects.get(pk=assignee_id)
        if target_user is None:
            message = '%s unassigned a user from the event' % (
                _format_user(activity.user),)
        elif activity.user is not None and target_user.id == activity.user.id:
            message = '%s assigned themselves to the event' % (
                _format_user(activity.user),)
        else:
            message = '%s assigned %s to the event' % (
                _format_user(activity.user),
                _format_user(target_user))
    elif activity.type == Activity.NOTE:
        message = '%s left a note on the event' % (
            _format_user(activity.user),)
    else:
        return

    event = activity.group.get_latest_event()
    Event.objects.bind_nodes([event], 'data')
    project = activity.project
    link = activity.group.get_absolute_url()

    legacy_message = (
        '%(project_name)s %(message)s (%(event)s, %(culprit)s) '
        '[<a href="%(link)s">view</a>]'
    ) % {
        'project_name': '<strong>%s</strong>' % escape(project.name),
        'event': escape(event.error()),
        'message': message,
        'culprit': escape(event.culprit),
        'link': escape(link),
    }

    return {
        'color': 'yellow',
        'message': legacy_message,
        'card': _make_event_card(activity.group, event, title=message,
                                 subtitle='%s, %s' % (event.error(),
                                                      event.culprit),
                                 compact=True),
        'format': 'html',
        'notify': False,
    }


def make_subscription_update_notification(new=None, removed=None):
    bits = ['The project subscriptions for this room were updated. ']

    def _proj(project):
        return '<strong>%s</strong>' % escape(project.name)

    if new:
        if len(new) == 1:
            bits.append('New project: %s. ' % _proj(new[0]))
        else:
            bits.append('New projects: %s. ' %
                        ', '.join(_proj(x) for x in new))
    if removed:
        if len(removed) == 1:
            bits.append('Removed project: %s' % _proj(removed[0]))
        else:
            bits.append('Removed projects: %s' %
                        ', '.join(_proj(x) for x in removed))
    return {
        'message': ' '.join(bits).strip(),
        'color': 'green',
        'notify': False,
    }


def make_generic_notification(text, color=None, notify=False):
    return {
        'message': escape(text),
        'color': color,
        'notify': notify,
    }
