from __future__ import absolute_import
from __future__ import unicode_literals

import json
import logging

from collections import OrderedDict

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from ..dot_ext.decorators import capability_protected_resource


ENCODED = settings.ENCODING

logger = logging.getLogger('hhs_server.%s' % __name__)

http_method_to_scope = {
    'GET': 'read',
    'HEAD': 'read',
    'PUT': 'write',
    'POST': 'write',
    'DELETE': 'write',
}


@capability_protected_resource()
def api_read(request):
    od = OrderedDict()
    od['hello'] = 'World'
    od['oauth2'] = True
    return HttpResponse(json.dumps(od, indent=4),
                        content_type='application/json')

# Example in curl calling this write API
# curl -H 'Content-Type: application/json' --data @test.json http://127.0.0.1:8000/api/write

# test.json just needs to be any valid JSON object {}.
# For example:
# {
#    'hello': 'World',
#    'oauth2': true,
# }
# This is just a sample write API.  It simply returns the provided object
# with the extra item:
# 'write': true


@capability_protected_resource()
@csrf_exempt
def api_write(request):
    if request.method == 'POST':
        errors = []
        try:
            if type(request.body) == bytes:
                decoded = request.body.decode(ENCODED)
            else:
                decoded = request.body
            j = json.loads(decoded, object_pairs_hook=OrderedDict)

            if not isinstance(j, OrderedDict):
                errors.append('The string did not contain a JSON object.')
            else:
                j['write'] = True
        except:
            errors.append('The string did not contain valid JSON.')
        if errors:
            response = OrderedDict()
            response['code'] = 400
            response['status'] = 'Error'
            response['message'] = 'Write Failed.'
            response['errors'] = errors
            return HttpResponse(json.dumps(response, indent=4),
                                content_type='application/json')
        # a valid JSON object was provided.
        return HttpResponse(json.dumps(j, indent=4),
                            content_type='application/json')
    # this is a GET
    response = OrderedDict()
    response['code'] = 200
    response['message'] = 'POST JSON as the body of the request to this URL.'
    return HttpResponse(json.dumps(response, indent=4),
                        content_type='application/json')
