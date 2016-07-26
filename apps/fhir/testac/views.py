#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: apps.fhir.testac.views
Created: 7/25/16 4:21 PM

File created by: Mark Scrimshire @ekivemark

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
from django.shortcuts import (render,
                              HttpResponse)
from django.utils.translation import ugettext_lazy as _

from ...cmsblue.cms_parser import (cms_text_read,
                                   parse_lines)
from ..bluebutton.utils import pretty_json
from .forms import input_packet


@login_required
def bb_upload(request, *args, **kwargs):
    """ Paste a BlueButton File for processing to FHIR """

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
                               'subname': "Create FHIR Test Data",
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
