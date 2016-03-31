#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from collections import OrderedDict
from django.http import HttpResponse
import json


def kickout_400(reason, status_code=400):

    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='exception'
    issue['details']= reason
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,     
                        content_type="application/json")


def kickout_401(reason, status_code=401):
    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='security'
    issue['details']= reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,     
                        content_type="application/json")

def kickout_403(reason, status_code=403):
    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='security'
    issue['details']= reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,     
                        content_type="application/json")


def kickout_404(reason, status_code=404):
    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='not-found'
    issue['details']= reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,     
                        content_type="application/json")


def kickout_500(reason, status_code=500):
    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='exception'
    issue['details']= reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,     
                        content_type="application/json")