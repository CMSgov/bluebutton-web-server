#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings
import json
from django.contrib.auth import login, authenticate
from httpauth import HttpBasicAuthentication
from django.http import HttpResponse




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
    body={"status": 401, "message": "Unauthorized - Your account credentials were invalid.", "num_results":0, "results": ()}
    if additional_info:
        body['message']="%s %s" % (body['message'], additional_info)
    body=json.dumps(body, indent=4)
    return body


def verify(verification_key):
    if SHA1_RE.search(verification_key):
        try:
            profile = RegistrationProfile.objects.get(activation_key=verification_key)
        except RegistrationProfile.DoesNotExist:
            return False
        if not profile.activation_key_expired():
            user = profile.user
            user.save()
            profile.activation_key = 'EMAIL_VERIFIED'
            profile.save()
            return user
    return False

