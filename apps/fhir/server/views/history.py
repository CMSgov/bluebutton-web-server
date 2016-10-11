import json

from collections import OrderedDict

from django.http import HttpResponse

from apps.fhir.fhir_core.utils import (kickout_400)

from .utils import check_access_interaction_and_resource_type


def history(request, resource_type, id):
    interaction_type = '_history'
    # Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type, interaction_type)
    if deny:
        # If not allowed, return a 4xx error.
        return deny

    # Read Search Interaction
    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/12345/_history
    if request.method != 'GET':
        msg = 'HTTP method %s not supported at this URL.' % (request.method)
        return kickout_400(msg)

    # testing direct response
    # return FHIR_BACKEND.history(request, resource_type, id)

    od = OrderedDict()
    od['request_method'] = request.method
    od['interaction_type'] = '_history'
    od['resource_type'] = resource_type
    od['id'] = id
    od['note'] = 'This is only a stub for future implementation'

    return HttpResponse(json.dumps(od, indent=4),
                        content_type='application/json')


def vread(request, resource_type, id, vid):
    interaction_type = 'vread'
    # Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type, interaction_type)
    if deny:
        # If not allowed, return a 4xx error.
        return deny

    # VRead Interaction
    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/12345/_history/1
    if request.method != 'GET':
        msg = 'HTTP method %s not supported at this URL.' % (request.method)
        return kickout_400(msg)

    # testing direct response
    # FIXME: FHIR_BACKEND not defined, it will raise a `NameError`
    # return FHIR_BACKEND.vread(request, resource_type, id, vid)
    return deny

    # FIXME: this part of code is unreachable
    od = OrderedDict()
    od['request_method'] = request.method
    od['interaction_type'] = 'vread'
    od['resource_type'] = resource_type
    od['id'] = id
    od['vid'] = vid
    od['note'] = 'This is only a stub for future implementation'

    return HttpResponse(json.dumps(od, indent=4),
                        content_type='application/json')
