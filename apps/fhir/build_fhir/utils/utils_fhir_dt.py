#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: ir-fhir
App: apps.fhir.build_fhir.utils
FILE: utils_fhir_data
Created: 7/24/16 12:09 PM

Created by: Mark Scrimshire @ekivemark, Medyear

Construct Fhir Data Type elements

"""
import json
from collections import OrderedDict
from datetime import datetime
from pytz import timezone

from django.conf import settings

from ...bluebutton.utils import pretty_json
from .utils import humanname_use, build_list_from

def dt_meta(vid=None, ):
    """ Construct Meta data type

{
  // from Element: extension
  "versionId" : "<id>", // Version specific identifier
  "lastUpdated" : "<instant>", // When the resource version last changed
  "profile" : ["<uri>"], // Profiles this resource claims to conform to
  "security" : [{ Coding }], // Security Labels applied to this resource
  "tag" : [{ Coding }] // Tags applied to this resource
}

    """
    dt = OrderedDict()
    if vid:
        str_vid = str(vid)
    else:
        str_vid = "1"
    dt["versionId"] = str_vid
    dt["lastUpdated"] = dt_instant()

    return pretty_json(dt)


def dt_identifier(id_value,
                  id_use="temp",
                  id_type=None,
                  id_system=None,
                  id_period=None,
                  id_assigner=None):
    """
        Construct an Identifer data type

    :param id_value:
    :param id_use:
    :return: {Identifier,}

    http://hl7-fhir.github.io/datatypes.html#Identifier
{
  // from Element: extension
  "use" : "<code>", // usual | official | temp | secondary (If known)
  "type" : { CodeableConcept }, // Description of identifier
  "system" : "<uri>", // The namespace for the identifier
  "value" : "<string>", // The value that is unique
  "period" : { Period }, // Time period when id is/was valid for use
  "assigner" : { Reference(Organization) } // Organization that issued id (may be just text)
}

    """

    dt = OrderedDict()
    dt['use'] = id_use
    if id_type:
        if isinstance(id_type, dict):
            dt['type'] = id_type
        else:
            dt['type'] = dt_codeable_concept(id_type)
    if id_system:
        dt['system'] = id_system
    if id_period:
        dt['period'] = id_period
    if id_assigner:
        dt['assigner'] = id_assigner

    return pretty_json(dt)


def dt_codeable_concept(concept):
    """ Format a codeable concept
        http://hl7-fhir.github.io/datatypes.html#CodeableConcept
{
  // from Element: extension
  "coding" : [{ Coding }], // Code defined by a terminology system
  "text" : "<string>" // Plain text representation of the concept
}

    """
    dt = OrderedDict()
    if isinstance(concept, dict):
        # Must be a valid codeable concept structure
        dt = concept
    elif isinstance(concept, list):
        for c in concept:
            # Must have coding and text in list item
            if isinstance(c, dict):
                dt.append(c)
            else:
                dt.append({"text": c})

    if len(dt) == 0:
        return None

    return pretty_json(dt)


def dt_instant(my_now=None):
    """ Format a json datetime in xs:datetime format

        .now(): 2012-02-17 09:52:35.033232
        datetime.datetime.now(pytz.utc).isoformat()
        '2012-02-17T11:58:44.789024+00:00'

    """
    if my_now:
        now_is = my_now
    else:
        now_is = datetime.now(timezone(settings.TIME_ZONE))

    format_now = now_is.isoformat()

    return format_now

def dt_human_name(id_name=None,
                  id_use=None,
                  id_prefix=None,
                  id_suffix=None,
                  id_period=None):
    """ Format a HumanName Resource element

    :param id_name:
    :param id_type:
    :param id_prefix:
    :param id_suffix:
    :param id_period: Must be in FHIR Period format
    :return:

{
  "resourceType" : "HumanName",
  // from Element: extension
  "use" : "<code>", // usual | official | temp | nickname | anonymous | old | maiden
  "text" : "<string>", // Text representation of the full name
  "family" : ["<string>"], // Family name (often called 'Surname')
  "given" : ["<string>"], // Given names (not always 'first'). Includes middle names
  "prefix" : ["<string>"], // Parts that come before the name
  "suffix" : ["<string>"], // Parts that come after the name
  "period" : { Period } // Time period when name was/is in use
}

    """
    if id_name is None:
        return None
    elif id_name == "":
        return None

    HumanName = OrderedDict()
    HumanName["resourceType"] = "HumanName"
    if id_use:
        set_use = humanname_use(id_use)
        if set_use:
            HumanName["use"] = set_use["use"]

    HumanName['text'] = id_name.rstrip()
    name = id_name.rstrip().split(' ')

    HumanName['family'] = [name[len(name) - 1]]
    HumanName['given'] = []
    ct = 0
    for n in name:
        if ct <= (len(name) - 2):
            HumanName['given'].append(n)
        ct += 1

    prefix = build_list_from("prefix", id_input=id_prefix)
    if prefix:
        HumanName['prefix'] = prefix['prefix']
    suffix = build_list_from("suffix", id_input=id_suffix)
    if suffix:
        HumanName['suffix'] = suffix['suffix']
    if id_period:
        HumanName['period'] = id_period

    return pretty_json(HumanName)
