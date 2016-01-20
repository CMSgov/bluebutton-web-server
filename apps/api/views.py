from django.shortcuts import render
from collections import OrderedDict
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

from oauth2_provider.decorators import protected_resource

# Hey Evonove - These are two sample RESTFul endpoints I'd like to protect as an example.
# Ideally we would use some sort of a decorator.  When the oauth request fails I want to
# return JSON (unless you think otherwise)

@protected_resource()
def api_read(request):
    od = OrderedDict()
    od['hello']="World"
    od['oauth2']=True
    return HttpResponse(json.dumps(od, indent=4),
                        content_type="application/json")

# Example in curl calling this write API
# curl -H "Content-Type: application/json" --data @test.json http://127.0.0.1:8000/api/write

# test.json just needs to be any valid JSON object {}.
# For example:
# {
#    "hello": "World",
#    "oauth2": true,
# }
# This is just a sample write API.  It simply returns the provided object
# with the extra item:
# "write": true


@protected_resource()
def api_write(request):
    if request.method == 'POST':

        errors =[]
        try:
            j =json.loads(request.body, object_pairs_hook=OrderedDict)
            print type(j)

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
    response['message'] =  "POST JSON as the body of the request to this URL."
    return HttpResponse(json.dumps(response, indent =4),
                                    content_type="application/json")
