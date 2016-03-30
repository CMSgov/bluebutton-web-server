import sys
from django.shortcuts import render
from ..models import SupportedResourceType
from collections import OrderedDict
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json, uuid
from jsonschema import validate, ValidationError
import datetime
from ..utils import (kickout_404, kickout_403, kickout_400, kickout_500)
from .hello import hello
from .search import search

@csrf_exempt
def create(request, resource_type):
    """Create FHIR Interaction"""
    # Example client use in curl:
    # curl -H "Content-Type: application/json" --data @test.json http://127.0.0.1:8000/fhir/Practitioner
    interaction_type = 'create'
    #re-route to hello if no resource type is given:
    if not resource_type:
        return hello(request)
    
    try:
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        if interaction_type not in rt.get_supported_interaction_types()  and request.method == "GET":
            #GET means that this is a search so re-route
            return search(request, resource_type)

        elif interaction_type not in rt.get_supported_interaction_types() :
            msg = "The interaction %s is not permitted on %s FHIR resources on this FHIR sever." % (interaction_type,
                                                                           resource_type)
            return kickout_403(msg)

    except SupportedResourceType.DoesNotExist:
        msg = "%s is not a supported resource type on this FHIR server." % (resource_type)
        return kickout_404(msg)

    # Catch all for GETs to re-direct to search if CREATE permission is valid
    if request.method == "GET":
        return search(request, resource_type)

    if request.method == 'POST':
                #Check if request body is JSON ------------------------
        try:
            j =json.loads(request.body, object_pairs_hook=OrderedDict)
            if type(j) !=  type({}):
                kickout_400("The request body did not contain a JSON object i.e. {}.")
        except:
            return kickout_400("The request body did not contain valid JSON.")
        
        if j.has_key('id'):
            return kickout_400("Create cannot have an id. Perhaps you meant to perform an update?")
        
        #check json_schema is valid
        try:
            json_schema = json.loads(rt.json_schema, object_pairs_hook=OrderedDict)
              
        except:
            return kickout_500("The JSON Schema on the server did not contain valid JSON.")
        
        #Check jsonschema
        if json_schema:
            try: 
                validate(j, json_schema)
            except ValidationError:
                msg = "JSON Schema Conformance Error. %s" % (str(sys.exc_info()[1][0]))
                return kickout_400(msg)
                 
        
        #write_to_mongo - TBD
        response = OrderedDict()
        response['id'] = str(uuid.uuid4())
        
        meta = OrderedDict()
        
        if j.get('meta').get('versionId'):
             meta['versionId'] = j.get('meta').get('versionId')
        else:
             meta['versionId'] = 1
        
        if j.get('meta').get('lastUpdated'):
             meta['lastUpdated'] = j.get('meta').get('lastUpdated')
        else:
             meta['lastUpdated'] = "%sZ" % (datetime.datetime.utcnow().isoformat())
        
        meta['id']       = response['id']
        response['meta'] = meta
        
        hr = HttpResponse(json.dumps(response, indent=4), status=201,
                                    content_type="application/json") 
        hr['Location'] = "%s/%s/%s/_history/%s" % (
                         "http://127.0.0.1:8000/fhir",
                         resource_type,
                         meta['id'],
                         meta['versionId'])
        return hr
    

        
        
        
    #This is something other than GET or POST (i.e. a  GET)
    if request.method not in ("GET", "POST"):
        od = OrderedDict()
        od['request_method']= request.method
        od['interaction_type'] = "create"
        od['resource_type']    = resource_type
        od['note'] = "Perform an HTTP POST to this URL with the JSON resource as the request body."
        
        
        return HttpResponse(json.dumps(od, indent=4),
                            content_type="application/json")
