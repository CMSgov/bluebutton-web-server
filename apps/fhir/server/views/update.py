import json

from collections import OrderedDict

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.fhir.server.mongofhirutils import update_mongo_fhir

from .utils import check_access_interaction_and_resource_type


@csrf_exempt
def update(request, resource_type, id):
    """
    Update FHIR Interaction

    Example client use in curl:
    curl -X PUT -H 'Content-Type: application/json' --data @test.json http://127.0.0.1:8000/fhir/Practitioner/12345
    """

    interaction_type = 'update'
    # Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type, interaction_type)
    if deny:
        # If not allowed, return a 4xx error.
        return deny

    od = update_mongo_fhir(json.loads(request.body, object_pairs_hook=OrderedDict), 'fhir', resource_type, id)

    if od['code'] == 200:
        return HttpResponse(json.dumps(od['result'], indent=4),
                            status=od['code'], content_type='application/json')
    else:
        oo = OrderedDict()
        oo['resourceType'] = 'OperationOutcome'
        oo['issue'] = []
        issue = OrderedDict()

        if od['code'] == 500:
            issue['severity'] = 'fatal'
            issue['code'] = 'exception'
            issue['details'] = od['details']

        if od['code'] == 400:
            issue['severity'] = 'fatal'
            issue['code'] = 'invalid'
            issue['details'] = od['details']
        oo['issue'].append(issue)

        return HttpResponse(json.dumps(oo, indent=4),
                            status=od['code'], content_type='application/json')
