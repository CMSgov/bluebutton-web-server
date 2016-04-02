from __future__ import absolute_import
from __future__ import unicode_literals

import json
import logging
from collections import OrderedDict

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.dot_ext.decorators import capability_protected_resource


@capability_protected_resource()
@csrf_exempt
def nppes_update(request):
    
    if request.method == 'POST':
        errors =[]
        try:
            j =json.loads(request.body, object_pairs_hook=OrderedDict)

            if type(j) !=  type(OrderedDict()):
                errors.append("The string did not contain a JSON object.")
            else:
                j['write'] = True
        except:
            errors.append("The string did not contain valid JSON.")
        if errors:
            response = OrderedDict()
            response['code']= 400
            response['status']= "Error"
            response['message']="Write Failed."
            response['errors']= errors
            return HttpResponse(json.dumps(response, indent =4),
                                           content_type="application/json")
        #A valid JSON object was provided.
        return HttpResponse(json.dumps(j, indent =4),
                                           content_type="application/json")
    #this is a GET
    response = OrderedDict()
    response['code'] = 200
    response['message'] =  "POST Provider JSON as the body of the request to this URL."
    return HttpResponse(json.dumps(response, indent =4),
                                    content_type="application/json")
