import json

from collections import OrderedDict

from django.http import HttpResponse

from apps.fhir.fhir_core.utils import kickout_400


def search(request, resource_type):
    """
    Search Interaction
    Example client use in curl:
    curl -X GET  http://127.0.0.1:8000/fhir/Practitioner?foo=bar
    """
    # FIXME: variable not used
    # interaction_type = 'search'

    if request.method != 'GET':
        msg = 'HTTP method %s not supported at this URL.' % (request.method)
        return kickout_400(msg)

    # Move to fhir_io_mongo (Plugable back-end)
    od = OrderedDict()
    od['request_method'] = request.method
    od['interaction_type'] = 'search'
    od['resource_type'] = resource_type
    od['search_params'] = request.GET
    od['note'] = 'This is only a stub for future implementation'

    return HttpResponse(json.dumps(od, indent=4),
                        content_type='application/json')
