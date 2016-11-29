from __future__ import absolute_import

import dateutil.parser
import hashlib
import hmac
import logging
import six

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.utils import timezone
from simplejson import JSONDecodeError
from sentry.models import (
    Commit, CommitAuthor, CommitFileChange, Organization, OrganizationOption,
    Repository
)
from sentry.utils import json

logger = logging.getLogger('sentry.webhooks')


class Webhook(object):
    def __call__(self, organization, event):
        raise NotImplementedError


class PushEventWebhook(Webhook):
    # https://developer.github.com/v3/activity/events/types/#pushevent
    def __call__(self, organization, event):
        authors = {}

        repo = Repository.objects.get_or_create(
            organization_id=organization.id,
            provider='github',
            external_id=event['repository']['full_name'],
        )[0]

        for commit in event['commits']:
            if not commit['distinct']:
                continue

            author_email = commit['author']['email']
            if '@' not in author_email:
                author_email = u'{}@localhost'.format(
                    author_email[:65],
                )

            # TODO(dcramer): we need to deal with bad values here, but since
            # its optional, lets just throw it out for now
            if len(author_email) > 75:
                author = None
            elif author_email not in authors:
                authors[author_email] = author = CommitAuthor.objects.get_or_create(
                    organization_id=organization.id,
                    email=author_email,
                    defaults={
                        'name': commit['author']['name'][:128],
                    }
                )[0]
                if author.name != commit['author']['name']:
                    author.update(name=commit['author']['name'])
            else:
                author = authors[author_email]

            try:
                with transaction.atomic():
                    c = Commit.objects.create(
                        repository_id=repo.id,
                        organization_id=organization.id,
                        key=commit['id'],
                        message=commit['message'],
                        author=author,
                        date_added=dateutil.parser.parse(
                            commit['timestamp'],
                        ).astimezone(timezone.utc),
                    )
                    for fname in commit['added']:
                        CommitFileChange.objects.create(
                            organization_id=organization.id,
                            commit=c,
                            filename=fname,
                            type='A',
                        )
                    for fname in commit['removed']:
                        CommitFileChange.objects.create(
                            organization_id=organization.id,
                            commit=c,
                            filename=fname,
                            type='D',
                        )
                    for fname in commit['modified']:
                        CommitFileChange.objects.create(
                            organization_id=organization.id,
                            commit=c,
                            filename=fname,
                            type='M',
                        )
            except IntegrityError:
                pass


class GithubWebhookEndpoint(View):
    _handlers = {
        'push': PushEventWebhook,
    }

    # https://developer.github.com/webhooks/
    def get_handler(self, event_type):
        return self._handlers.get(event_type)

    def is_valid_signature(self, method, body, secret, signature):
        if method == 'sha1':
            mod = hashlib.sha1
        else:
            raise NotImplementedError('signature method %s is not supported' % (
                method,
            ))
        expected = hmac.new(
            key=secret.encode('utf-8'),
            msg=body,
            digestmod=mod,
        ).hexdigest()
        return constant_time_compare(expected, signature)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if request.method != 'POST':
            return HttpResponse(status=405)

        return super(GithubWebhookEndpoint, self).dispatch(request, *args, **kwargs)

    def post(self, request, organization_id):
        try:
            organization = Organization.objects.get_from_cache(
                id=organization_id,
            )
        except Organization.DoesNotExist:
            logger.error('github.webhook.invalid-organization', extra={
                'organization_id': organization_id,
            })
            return HttpResponse(status=400)

        secret = OrganizationOption.objects.get_value(
            organization=organization,
            key='github:webhook_secret',
        )
        if secret is None:
            logger.error('github.webhook.missing-secret', extra={
                'organization_id': organization.id,
            })
            return HttpResponse(status=401)

        body = six.binary_type(request.body)
        if not body:
            logger.error('github.webhook.missing-body', extra={
                'organization_id': organization.id,
            })
            return HttpResponse(status=400)

        try:
            handler = self.get_handler(request.META['HTTP_X_GITHUB_EVENT'])
        except KeyError:
            logger.error('github.webhook.missing-event', extra={
                'organization_id': organization.id,
            })
            return HttpResponse(status=400)

        if not handler:
            return HttpResponse(status=204)

        try:
            method, signature = request.META['HTTP_X_HUB_SIGNATURE'].split('=', 1)
        except (KeyError, IndexError):
            logger.error('github.webhook.missing-signature', extra={
                'organization_id': organization.id,
            })
            return HttpResponse(status=400)

        if not self.is_valid_signature(method, body, secret, signature):
            logger.error('github.webhook.invalid-signature', extra={
                'organization_id': organization.id,
            })
            return HttpResponse(status=401)

        try:
            event = json.loads(body.decode('utf-8'))
        except JSONDecodeError:
            logger.error('github.webhook.invalid-json', extra={
                'organization_id': organization.id,
            }, exc_info=True)
            return HttpResponse(status=400)

        handler()(organization, event)
        return HttpResponse(status=204)
