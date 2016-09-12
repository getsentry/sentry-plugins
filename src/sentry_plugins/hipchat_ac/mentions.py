from __future__ import absolute_import

import json
import time

from sentry.utils.dates import to_datetime, to_timestamp
from sentry.models import Project, Group, Event

from django.utils import timezone
from django.conf import settings


MAX_RECENT = 15
RECENT_HOURS = 24 * 30


# The Redis cluster manager (``clusters``) was added in Sentry 8.2 (GH-2714)
# and replaces ``make_rb_cluster`` (which will be removed in a future version.)
try:
    from sentry.utils.redis import clusters
    cluster = clusters.get('default')
except ImportError:
    from sentry.utils.redis import make_rb_cluster
    cluster = make_rb_cluster(settings.SENTRY_REDIS_OPTIONS['hosts'])


def get_key(tenant):
    return 'sentry-hipchat-ac:%s:mentions' % tenant.id


def get_recent_mentions(tenant):
    client = cluster.get_routing_client()
    key = get_key(tenant)
    ids = [x for x in client.zrangebyscore(
        key, time.time() - (RECENT_HOURS * 60), '+inf')][-MAX_RECENT:]

    with cluster.map() as map_client:
        items = [map_client.get('%s:%s' % (key, id)) for id in ids]
    items = [json.loads(x.value) for x in items if x.value is not None]

    projects = items and dict((x.id, x) for x in Project.objects.filter(
        pk__in=[x['project'] for x in items],
    )) or {}
    groups = items and dict((x.id, x) for x in Group.objects.filter(
        pk__in=[x['group'] for x in items],
    )) or {}
    events = items and dict((x.id, x) for x in Event.objects.filter(
        pk__in=[x['event'] for x in items if x['event'] is not None],
    )) or {}

    for item in items:
        item['project'] = projects.get(item['project'])
        item['group'] = groups.get(item['group'])
        item['event'] = events.get(item['event'])
        if item['event'] is None and item['group'] is not None:
            item['event'] = item['group'].get_latest_event()
        item['last_mentioned'] = to_datetime(item['last_mentioned'])

    return items


def count_recent_mentions(tenant):
    client = cluster.get_routing_client()
    key = get_key(tenant)
    return min(MAX_RECENT, client.zcount(
        key, time.time() - (RECENT_HOURS * 60), '+inf'))


def clear_tenant_mentions(tenant):
    client = cluster.get_routing_client()
    key = get_key(tenant)
    client.delete(key)


def clear_project_mentions(tenant, projects):
    client = cluster.get_routing_client()
    project_ids = set([x.id for x in projects])
    key = get_key(tenant)
    ids = client.zrange(key, 0, -1)
    with cluster.map() as map_client:
        items = [map_client.get('%s:%s' % (key, id)) for id in ids]
    items = [json.loads(x.value) for x in items if x.value is not None]

    to_remove = []
    for item in items:
        if item['project'] in project_ids:
            to_remove.append('%s/%s' % (item['group'], item['event'] or '-'))

    if to_remove:
        client.zrem(key, *to_remove)


def mention_event(project, group, tenant, event=None):
    ts = to_timestamp(timezone.now())
    id = '%s/%s' % (group.id, event.id if event is not None else '-')
    item = json.dumps({
        'project': project.id,
        'group': group.id,
        'event': event.id if event is not None else None,
        'last_mentioned': ts,
    })

    expires = (RECENT_HOURS + 1) * 60 * 60
    with cluster.map() as client:
        key = get_key(tenant)
        client.zadd(key, ts, id)
        client.expire(key, expires)
        client.setex('%s:%s' % (key, id), expires, item)
        client.zremrangebyscore(key, '-inf', time.time() - (RECENT_HOURS * 60))
        client.zremrangebyrank(key, 0, -MAX_RECENT - 1)
