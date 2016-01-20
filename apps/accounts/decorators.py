#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4


"""
    Decorator to check for credentials before responding on API requests.
    REsponse with JSON instead of standard login redirect.
"""

import urlparse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.decorators import available_attrs
from functools import update_wrapper, wraps
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate, login
import json, string, random
from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from datetime import date

def json_login_required(func):
    """
        Put this decorator before your view to check if the user is logged in
        and return a JSON 401 error if he/she is not.
    """
    
    def wrapper(request, *args, **kwargs):
        user= None
        #get the Basic username and password from the request.
        auth_string = request.META.get('HTTP_AUTHORIZATION', None)
        
        if auth_string:
            (authmeth, auth) = auth_string.split(" ", 1)
            auth = auth.strip().decode('base64')
            (username, password) = auth.split(':', 1)

        
            #print username, password  
            user = authenticate(username=username, password=password)
        
        if not user or not user.is_active:
            return HttpResponse(unauthorized_json_response(),
                    mimetype="application/json")          
        login(request, user)
        return func(request, *args, **kwargs)

    return update_wrapper(wrapper, func)



def authorize(request):
    a=HttpBasicAuthentication()
    if a.is_authenticated(request):
        login(request,request.user)
        auth=True
    else:
        if request.user.is_authenticated():
            auth=True
        else:
            auth=False
    return auth

def unauthorized_json_response(additional_info=None):
    body={"code": 401,
          "message": "Unauthorized - Your account credentials were invalid.",
          "errors": [ "Unauthorized - Your account credentials were invalid.", ]
          }
    if additional_info:
        body['message']="%s %s" % (body['message'], additional_info)
    body=json.dumps(body, indent=4, )
    return body
