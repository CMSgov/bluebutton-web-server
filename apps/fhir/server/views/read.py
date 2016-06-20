import json

from collections import OrderedDict

from django.http import HttpResponse

from .utils import check_access_interaction_and_resource_type


def read(request, resource_type, id):
    """
    Read FHIR Interaction
    Example client use in curl:
    curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """
    interaction_type = 'read'
    # Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type, interaction_type)
    if deny:
        # If not allowed, return a 4xx error.
        return deny

    od = OrderedDict()
    od['request_method'] = request.method
    od['interaction_type'] = interaction_type
    od['resource_type'] = resource_type
    od['id'] = id
    od['note'] = 'This is only a stub for future implementation'
    return HttpResponse(json.dumps(od, indent=4),
                        content_type='application/json')
