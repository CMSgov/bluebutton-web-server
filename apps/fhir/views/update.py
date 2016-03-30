from django.shortcuts import render
from collections import OrderedDict
from django.http import HttpResponse
from ..utils import (kickout_403, kickout_404)
import json
from django.views.decorators.csrf import csrf_exempt
from ..models import SupportedResourceType
from .utils import check_access_interaction_and_resource_type

@csrf_exempt
def update(request, resource_type, id):
    """Update FHIR Interaction"""
    # Example client use in curl:
    # curl -X PUT -H "Content-Type: application/json" --data @test.json http://127.0.0.1:8000/fhir/Practitioner/12345
    
    interaction_type = 'update'
    #Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type, interaction_type)
    if deny:
        #If not allowed, return a 4xx error.
        return deny

    # Replace Section below with call to function in fhir_io_mongo or pluggable backend
    od = OrderedDict()
    od['request_method']= request.method
    od['interaction_type'] = "update"
    od['resource_type']    = resource_type
    od['id'] = id
    od['note'] = "This is only a stub for future implementation"
    return HttpResponse(json.dumps(od, indent=4),
                        content_type="application/json")