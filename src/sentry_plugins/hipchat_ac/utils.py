from __future__ import absolute_import

import os
import json

from django.http import HttpResponse


IS_DEBUG = os.environ.get('AC_DEBUG') == '1'


class JsonResponse(HttpResponse):

    def __init__(self, value, status=200):
        HttpResponse.__init__(self, json.dumps(value), status=status,
                              content_type='application/json')
