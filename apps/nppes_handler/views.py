from __future__ import absolute_import
from __future__ import unicode_literals

import json, sys
import logging
from collections import OrderedDict

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.dot_ext.decorators import capability_protected_resource
from .mongoutils import update_mongo_pjson
from pdt.pjson.validate_pjson import validate_pjson


@capability_protected_resource()
@csrf_exempt
def nppes_update(request):
    
    response = OrderedDict()
    response['code']= 000
    response['status']= ""
    response['message']=""
    errors = []
    
    if request.method == 'POST':
        try:
            j =json.loads(request.body, object_pairs_hook=OrderedDict)
            response = validate_pjson(request.body, "update")
        except:
            errors.append("The string did not contain valid JSON.")
        
        if response['errors']:
            for e in response['errors']:
                errors.append(e)
        
        if errors:
            response = OrderedDict()
            response['code']= 400
            response['status']= "Error"
            response['message']="The NPPES update failed."
            response['errors']= errors
            
        else:
            #Looks good
            
            nppes_write_response = update_mongo_pjson(j)

            
            response['code']= nppes_write_response['code']
            if response['code'] == 200:
                response['status']= "OK"
                response['message']="The NPPES update for %s succeeded."  % (nppes_write_response['number'])
            else:
                response['status']= "FAIL"
                response['message']="The NPPES update for %s failed."  % (nppes_write_response['number'])               
                response['errors'] = nppes_write_response['errors']
                
        return HttpResponse(json.dumps(response, indent =4),
                                           content_type="application/json")
    #this is a GET
    response = OrderedDict()
    response['code'] = 200
    response['message'] =  "POST Provider JSON as the body of the request to this URL."
    return HttpResponse(json.dumps(response, indent =4),
                                    content_type="application/json")
