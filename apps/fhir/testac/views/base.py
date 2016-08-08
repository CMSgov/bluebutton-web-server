#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Activate User

- Create Crosswalk
- Create Form for BlueButton Upload
- Parse BlueButton upload to JSON
- Create Patient Record as FHIR Resource
- Post FHIR Patient to Backend
- Get Patient/Id
- Update CrossWalk
- Parse Claims
- Check Dates in Claims
- Update Dates if too old
- Create FHIR EOBs
- Post to back-end FHIR server

"""
import json
import logging
import requests

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import (render,
                              HttpResponse,
                              HttpResponseRedirect)
from django.utils.translation import ugettext_lazy as _


from apps.cmsblue.cms_parser import (cms_text_read,
                                     parse_lines)
from ...bluebutton.utils import pretty_json, FhirServerUrl
from ..forms import input_packet
from ...bluebutton.models import Crosswalk

from ...build_fhir.utils.fhir_resource_version import FHIR_CONTENT_TYPE_JSON
from ...build_fhir.views.base import build_patient
from ..utils.utils import (get_posted_resource_id,
                           update_crosswalk,
                           get_bb_claims)

from ...build_fhir.views.rt_explanationofbenefit import build_eob
logger = logging.getLogger('hhs_server.%s' % __name__)


@login_required
def bb_upload(request, *args, **kwargs):
    """ Paste a BlueButton File for processing to FHIR

        access via check_crosswalk first to make sure a
        link to the FHIR backend is not in place.

    """

    name = 'Upload Blue Button Text Content'
    additional_info = """
    <p>Paste the contents of a Blue Button Text File into this form
    and we will convert it and create FHIR Patient and Claims
    (ExplanationOfBenefit) resources to help you test the Blue Button API.
    </p>

    """
    if request.method == 'POST':
        output_fmt = "html"
        form = input_packet(request.POST)
        if form.is_valid():

            output_fmt = form.cleaned_data['output_format']

            content = form.cleaned_data['bb_text']

            # Now send to Blue Button parser
            json_stuff = bb_to_xwalk(request, content)

            if "json" in output_fmt:
                # print("We got some BlueButton Text")
                return HttpResponse(pretty_json(json_stuff),
                                    content_type=FHIR_CONTENT_TYPE_JSON)
            else:
                messages.success(
                    request,
                    _('Your Blue Button text file is being processed '))

                return render(request,
                              'testac/output.html',
                              {'content': pretty_json(json_stuff),
                               'output': json_stuff,
                               'subname': "Upload BlueButton Text",
                               'button': "Check record again",
                               'button_link': "/"}
                              )
        else:
            return render(request, 'generic/bootstrapform.html', {
                'name': name,
                'form': form,
                'additional_info': additional_info,
            })
    else:
        # this is an HTTP  GET
        return render(request,
                      'generic/bootstrapform.html',
                      {'name': name,
                       'form': input_packet(),
                       'additional_info': additional_info})


@login_required
def check_crosswalk(request, *args, **kwargs):
    """ Check for CrossWalk for this user """

    try:
        xwalk = Crosswalk.objects.get(user=request.user)

        if xwalk.fhir_id:
            # print("FHIR_ID:%s" % xwalk.fhir_id)
            messages.error(request,
                           _('Account is already linked to a FHIR resource.'))
            return HttpResponseRedirect(reverse_lazy('home'))
        # Crosswalk record exists but fhir_id is not defined

    except Crosswalk.DoesNotExist:
        # No record in Crosswalk
        # Create a Crosswalk record
        xwalk = Crosswalk()
        xwalk.user = request.user
        # We may want to add the default FHIR Server to the crosswalk entry
        # before we save.
        # xwalk.fhir_source =
        xwalk.save()

    # We didn't find a Crosswalk entry so we can go ahead and do an upload

    return bb_upload(request, *args, **kwargs)


def fhir_build_patient(request, bb_json):
    """ Construct a FHIR Patient Resource from bb_json

    "patient": {
        "patient": {
            "patient": "Demographic"
        },
        "source": "MyMedicare.gov",
        "name": "JOHN DOE",
        "dateOfBirth": "19100101",
        "address": {
            "addressType": "",
            "addressLine1": "123 ANY ROAD",
            "addressLine2": "",
            "city": "ANYTOWN",
            "state": "VA",
            "zip": "00001"
        },
        "phoneNumber": [
            "123-456-7890"
        ],
        "email": "JOHNDOE@example.com",
        "medicare": {
            "partAEffectiveDate": "20120101",
            "partBEffectiveDate": "20120101"
        }
    },


    """
    # Process the patient segment in bb_json
    if "patient" in bb_json:
        fhir_patient = pretty_json(build_patient(bb_json))
    else:
        return

    # print("\nFHIR_Patient:%s" % fhir_patient)

    fhir_server = FhirServerUrl() + "Patient"
    # print("Target URL:%s" % fhir_server)

    headers = {'content-type': FHIR_CONTENT_TYPE_JSON}
    fhir_result = requests.post(fhir_server,
                                data=fhir_patient,
                                headers=headers)

    # print("FHIR_Result:%s" % fhir_result.text)

    return fhir_result


def bb_to_xwalk(request, content):
    """ process bbfile to xwalk """

    # Now send to Blue Button parser
    bb_dict = cms_text_read(content)
    json_stuff = parse_lines(bb_dict)

    # Use json_stuff to build Patient Record
    outcome = fhir_build_patient(request,
                                 json.loads(json_stuff))
    id = get_posted_resource_id(outcome.json(), outcome.status_code)
    if id:
        # Now we can update the Crosswalk with patient_id
        cx = update_crosswalk(request, id)
        # We now have the Crosswalk updated

    else:
        messages.error(request, ("We had a problem allocating "
                       "a Patient/ID %s" % id))
        return json_stuff

    # We have a patient/id
    # Next we can write the EOBs
    eob_stuff = bb_to_eob(id, json_stuff)
    if 'resourceId' in eob_stuff:
        eob_stuff['resourceId'].append(cx.fhir_id)
    fhir_stuff = eob_stuff
    # Get Patient Resource add to fhir-stuff

    # Get EOBs for Patient - add to fhir_stuff

    return fhir_stuff


def bb_to_eob(patient_id, json_stuff):
    """ Take BB claims and create EOBs for Patient/id """

    eob_stuff = {}
    eob_resource = []
    eob_id = []
    claims = get_bb_claims(json_stuff)

    for claim in claims:
        # Construct data for EOB
        # eob_info =
        # write EOB
        rt = build_eob(patient_id, claim)
        rt_id = None
        if rt:
            # Get EOB/Id
            rt_id = write_resource(rt)
            if rt_id:
                eob_resource.append(rt)
                eob_id.append(rt_id)
        # Read EOB and add to eob_stuff

    eob_stuff = {"resourceId": eob_id,
                 "resource": eob_resource}
    return eob_stuff


def write_resource(rt):
    """ Write a Resource and get the Id """

    if "resourceType" not in rt:
        # No resource to deal with
        return

    fhir_server = FhirServerUrl() + rt['resourceType']
    # print("Target URL:%s" % fhir_server)

    headers = {'content-type': FHIR_CONTENT_TYPE_JSON}

    outcome = requests.post(fhir_server,
                            data=pretty_json(rt),
                            headers=headers)

    # logger.debug("status_code:%s"
    #              "\nOutcome:%s"
    #              "\nPost:%s" % (outcome.status_code,
    #                             outcome.json(),
    #                             pretty_json(rt)))

    # print("\nOutcome of write for [%s]:%s" % (rt['resourceType'],
    #                                           outcome.json()))
    id = get_posted_resource_id(outcome.json(), outcome.status_code)

    return id
