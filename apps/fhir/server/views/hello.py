import json

from collections import OrderedDict

from django.http import HttpResponse

from apps.fhir.server.models import SupportedResourceType


def hello(request):
    """
    Hello FHIR
    Example client use in curl:
    curl http://127.0.0.1:8000/fhir/hello
    """
    res_types = SupportedResourceType.objects.all()
    interactions = []
    for r in res_types:
        rt = OrderedDict()
        rt[r.resource_name] = r.get_supported_interaction_types()
        interactions.append(rt)
    od = OrderedDict()
    od['request_method'] = request.method
    od['resources_and_interaction_types'] = interactions
    od['note'] = 'Hello.  Welcome to the FHIR Server.'
    return HttpResponse(json.dumps(od, indent=4),
                        content_type='application/json')
