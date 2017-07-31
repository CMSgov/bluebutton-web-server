#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from __future__ import absolute_import
from __future__ import unicode_literals
import sys
import json
import logging
import os
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import Application
from ...capabilities.models import ProtectedCapability
from collections import OrderedDict
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from django.conf import settings


logger = logging.getLogger('hhs_server.%s' % __name__)


@require_POST
@csrf_exempt
def register(request):
    # If disabled
    if settings.DCRP == "":
        return JsonResponse({"error": "forbidden",
                             "error_description": "DCRP is disabled."},
                            status=401)
    # Have a look at the content
    r = check_for_json(request.body)
    if 'error' in r:
        return JsonResponse(r, status=400)
    else:
        r = check_contents(r)
    if 'error' in r:
        return JsonResponse(r, status=400)
    # Create the user for dcrp if not alreay exist
    dcrp_user, s = User.objects.get_or_create(
        username="dcrp",
        password="",
        is_active=False)

    a = Application
    a = Application.objects.create(name=r['client_name'],
                                   redirect_uris=r['redirect_uris'],
                                   user=dcrp_user,
                                   client_type=r['client_type'],
                                   authorization_grant_type=r['grant_types'][0])

    if 'scope' not in r:
        # Set default scopes since scope was ommited from the request
        scopelist = ["openid", "profile", "patient/Patient.read", "patient/ExplanationOfBenefit.read",
                     "patient/Organization.read", "patient/Coverage.read"]
        for s in scopelist:
            a.scope.add(ProtectedCapability.objects.get(
                slug=s, group__name="BlueButton"))
    else:
        # scopes were specified so only add those.
        for s in r['scope']:
            a.scope.add(ProtectedCapability.objects.get(slug=s))

    out = ""
    for s in a.scope.all():
        out = "%s %s" % (out, s.scope())
        out = out.lstrip().rstrip()

    r = {"client_id": a.client_id,
         "client_secret": a.client_secret,
         "redirect_uris": a.redirect_uris,
         "client_type": a.client_type,
         "grant_types": [a.authorization_grant_type, ],
         "scope": out}

    return JsonResponse(r)


def check_for_json(request_body):
    try:
        j = json.loads(str(request_body.decode('utf-8')),
                       object_pairs_hook=OrderedDict)
        if not isinstance(j, type(OrderedDict())):
            return {"error": "invalid_client_metadata",
                    "erros_desscription": "The request body did not contain a JSON object."}
    except:
        return {"error": "invalid_client_metadata",
                "error_description": "The request body did not contain valid JSON"
                }
    return j


def check_contents(j,
                   schema_fp=os.path.join(os.path.dirname(__file__),
                                          "..",
                                          "dcrp-json-schema.json")):
    schema_fh = open(schema_fp)
    s = json.loads(schema_fh.read(), object_pairs_hook=OrderedDict)
    try:
        validate(j, s)
    except ValidationError:
        return {"error": "invalid_client_metadata",
                "error_description": sys.exc_info()[1].message}

    if Application.objects.filter(name=j['client_name']).exists():
        return {"error": "invalid_client_metadata",
                "error_description":
                "client_name %s is already registered." % (j['client_name'])}
    if "scope" in j:
        scope = j['scope'].rstrip().lstrip()
        scopelist = scope.split(" ")
        for s in scopelist:
            if not ProtectedCapability.objects.filter(slug=s, group__name="BlueButton").exists():
                return {"error": "invalid_client_metadata",
                        "error_description":
                        "scope %s is invalid." % (s)}
        j['scope'] = scopelist

    return j
