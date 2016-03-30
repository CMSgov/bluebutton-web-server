#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from collections import OrderedDict
from django.http import HttpResponse
import json


def kickout_400(reason, status_code=400):
    response= OrderedDict()
    response["code"] = status_code
    response["errors"] = [reason,]
    return HttpResponse(json.dumps(response, indent = 4),
                        status=status_code,     
                        content_type="application/json")


def kickout_401(reason, status_code=401):
    response= OrderedDict()
    response["code"] = status_code
    response["errors"] = [reason,]
    return HttpResponse(json.dumps(response, indent = 4),
                        status=status_code,     
                        content_type="application/json")


def kickout_403(reason, status_code=403):
    response= OrderedDict()
    response["code"] = status_code
    response["errors"] = [reason,]
    return HttpResponse(json.dumps(response, indent = 4),
                        status=status_code,
                        content_type="application/json")


def kickout_404(reason, status_code=404):
    response= OrderedDict()
    response["code"] = status_code
    response["errors"] = [reason,]
    return HttpResponse(json.dumps(response, indent = 4),
                        status=status_code, 
                        content_type="application/json")


def kickout_500(reason, status_code=500):
    response= OrderedDict()
    response["code"] = status_code
    response["errors"] = [reason,]
    return HttpResponse(json.dumps(response, indent = 4),
                        status=status_code, 
                        content_type="application/json") 