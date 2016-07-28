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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import (render,
                              HttpResponse,
                              HttpResponseRedirect)
from django.utils.translation import ugettext_lazy as _


from apps.cmsblue.cms_parser import (cms_text_read,
                                   parse_lines)
from ...bluebutton.utils import pretty_json
from ..forms import input_packet
from ...bluebutton.models import Crosswalk


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
            bb_dict = cms_text_read(content)
            json_stuff = parse_lines(bb_dict)

            if "json" in output_fmt:
                # print("We got some BlueButton Text")
                return HttpResponse(pretty_json(json_stuff),
                                    content_type="application/json")
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

    if "patient" in bb_json:
        pass
    else:
        return None

    # Process the patient segment in bb_json
