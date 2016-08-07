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
import logging
import re

from collections import OrderedDict
from datetime import datetime
from pytz import timezone

from django.conf import settings
from django.utils.timezone import get_current_timezone

from .fhir_code_sets import (FHIR_IDENTIFIER_USE_CODE,
                             FHIR_CONTACTPOINT_SYSTEM_CODE,
                             FHIR_ADDRESS_USE_CODE,
                             FHIR_ADDRESS_TYPE_CODE)

from .utils import (human_name_use,
                    build_list_from,
                    use_code,
                    )

logger = logging.getLogger('hhs_server.%s' % __name__)


def dt_meta(vid=None, last_updated=None):
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
    my_now = dt_instant(my_now=last_updated)

    # print("\nSource DateTime:%s" % last_updated)
    # print("My_now:%s" % my_now)

    dt["lastUpdated"] = my_now

    # print("dt:%s" % dt)

    # return pretty_json(dt)
    return dt


def dt_identifier(id_value,
                  id_use=None,
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

    if not id_value:
        return

    # We have a value to represent

    dt = OrderedDict()

    if id_use:
        dt_use = use_code(id_use, FHIR_IDENTIFIER_USE_CODE)
        dt['use'] = dt_use
        if isinstance(id_type, dict):
            dt['type'] = id_type
        else:
            dt_type = dt_codeable_concept(id_type)
            if dt_type:
                dt['type'] = dt_type
    if id_system:
        dt['system'] = id_system

    dt['value'] = str(id_value)

    if id_period:
        dt['period'] = id_period
    if id_assigner:
        dt['assigner'] = id_assigner
        # TODO: Define dt_organization

    # return pretty_json(dt)
    return dt


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
            for k, v in c:
                # Must have coding and text in list item
                if isinstance(v, dict):
                    dt[k] = v
                else:
                    dt['text'] = v
    elif isinstance(concept, str):
        dt["text"] = concept

    if len(dt) == 0:
        return

    # return pretty_json(dt)
    return dt


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
        return
    elif id_name == "":
        return

    HumanName = OrderedDict()
    HumanName["resourceType"] = "HumanName"
    if id_use:
        set_use = human_name_use(id_use)
        if set_use:
            HumanName["use"] = set_use

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

    # return pretty_json(HumanName)
    return HumanName


def dt_coding(coding_dict=None):
    """ Construct a Coding Data Type

{
  // from Element: extension
  "system" : "<uri>", // Identity of the terminology system
  "version" : "<string>", // Version of the system - if relevant
  "code" : "<code>", // Symbol in syntax defined by the system
  "display" : "<string>", // Representation defined by the system
  "userSelected" : <boolean> // If this coding was chosen directly by the user
}

    All fields are optional

    """
    dt = OrderedDict()

    if coding_dict is None:
        return None

    if not isinstance(coding_dict, dict):

        return None

    # We have something to code

    if 'system' in coding_dict:
        dt['system'] = coding_dict['system']
    if 'version' in coding_dict:
        dt['version'] = coding_dict['version']
    if 'code' in coding_dict:
        dt['code'] = coding_dict['code']
    if 'display' in coding_dict:
        dt['display'] = coding_dict['display']
    if 'userSelected' in coding_dict:
        dt['userSelected'] = coding_dict['userSelected']

    # return pretty_json(dt)
    return dt


def dt_period(start_date=None, end_date=None):
    """ Create a Period Data Type

{
  // from Element: extension
  "start" : "<dateTime>", // C? Starting time with inclusive boundary
  "end" : "<dateTime>" // C? End time with inclusive boundary, if not ongoing
}
    """

    if not start_date and not end_date:
        # Nothing to do
        return None

    dt = OrderedDict()
    if isinstance(start_date, datetime):
        # We have a datetime to deal with
        dt['start'] = dt_instant(start_date)

    elif isinstance(start_date, str):
        # It is already a string
        # We will assume it in the correct format
        # as returned from dt_instant()

        dt['start'] = start_date

    if isinstance(end_date, datetime):
        # we have an end date
        # We will assume it in the correct format
        # as returned from dt_instant()
        dt['end'] = dt_instant(end_date)

    elif isinstance(end_date, str):
        dt['end'] = end_date

    #  We now need to check that start_date < end_date

    if start_date and end_date:
        if start_date > end_date:
            # We have an error situation
            logger.error("%s > %s" % (start_date,
                                      end_date))

    # return pretty_json(dt)
    return dt


def dt_contactpoint(cp_value, cp_system, use=None, rank=None, period=None):
    """ Create a ContactPoint Data Type

{
  "resourceType" : "ContactPoint",
  // from Element: extension
  "system" : "<code>", // C? phone | fax | email | pager | other
  "value" : "<string>", // The actual contact point details
  "use" : "<code>", // home | work | temp | old | mobile - purpose of this contact point
  "rank" : "<positiveInt>", // Specify preferred order of use (1 = highest)
  "period" : { Period } // Time period when the contact point was/is in use
}

    https://www.hl7.org/fhir/datatypes.html#ContactPoint

     """

    dt = OrderedDict()
    dt['resourceType'] = "ContactPoint"

    # system required if value is provided

    if cp_value:
        dt_system = use_code(cp_system,
                             code_set=FHIR_CONTACTPOINT_SYSTEM_CODE)
        if dt_system and cp_value:
            dt['system'] = dt_system
            dt['value'] = str(cp_value)
        else:
            logger.error("%s needs a system "
                         "definition. (%s) not found "
                         "in [%s]" % (cp_value,
                                      dt_system,
                                      FHIR_CONTACTPOINT_SYSTEM_CODE))
            return
    if use:
        dt_use = use_code(use, code_set=FHIR_IDENTIFIER_USE_CODE)
        if dt_use:
            dt['use'] = dt_use

    if rank:
        dt['rank'] = str(rank)

    if period:
        dt['period'] = period

    # return pretty_json(dt)
    return dt


def dt_address(a_address, a_use=None, a_type=None, a_text=None):
    """ Create Address Data Type
{
  "resourceType" : "Address",
  // from Element: extension
  "use" : "<code>", // home | work | temp | old - purpose of this address
  "type" : "<code>", // postal | physical | both
  "text" : "<string>", // Text representation of the address
  "line" : ["<string>"], // Street name, number, direction & P.O. Box etc.
  "city" : "<string>", // Name of city, town etc.
  "district" : "<string>", // District name (aka county)
  "state" : "<string>", // Sub-unit of country (abbreviations ok)
  "postalCode" : "<string>", // Postal code for area
  "country" : "<string>", // Country (can be ISO 3166 3 letter code)
  "period" : { Period } // Time period when address was/is in use
}

pt_json['patient]:
        "address": {
            "addressType": "",
            "addressLine1": "123 ANY ROAD",
            "addressLine2": "",
            "city": "ANYTOWN",
            "state": "VA",
            "zip": "00001"
        },

    """

    dt = OrderedDict()
    dt['resourceType'] = "Address"

    if a_use:
        dt_use = use_code(a_use, code_set=FHIR_ADDRESS_USE_CODE)
        if dt_use:
            dt['use'] = dt_use

    if a_type:
        dt_type = use_code(a_type, code_set=FHIR_ADDRESS_TYPE_CODE)
        if dt_type:
            dt['type'] = dt_type

    if a_text:
        dt['text'] = a_text

    if a_address:
        if 'addressType' in a_address:
            dt_type = use_code(a_address['addressType'],
                               code_set=FHIR_ADDRESS_TYPE_CODE)
            if dt_type:
                dt['type'] = dt_type
        a_line = []
        if 'addressLine1' in a_address:
            a_line.append(a_address['addressLine1'])
        if 'addressLine2' in a_address:
            a_line.append(a_address['addressLine2'])
        if len(a_line) > 0:
            dt['line'] = a_line

        if 'city' in a_address:
            dt['city'] = a_address['city']

        if 'state' in a_address:
            dt['state'] = a_address['state']

        if 'zip' in a_address:
            dt['postalCode'] = str(a_address['zip'])

        if 'country' in a_address:
            dt['country'] = a_address['country']

        if 'period' in a_address:
            dt['period'] = a_address['period']

    if len(dt) > 1:
        # return pretty_json(dt)
        return dt

    return


def date_yymmdd(t_date=None):
    """ Convert Text Date in YYMMDD to dt_instant """

    if not t_date:
        return

    format = "%Y%m%d"
    tz = get_current_timezone()

    now_is = datetime.strptime(t_date, format)
    my_now = tz.localize(now_is)

    d_date = dt_instant(my_now)

    return d_date


def name_drop_md(name):
    """ Drop the MD from the end of a name

        This is needed so that name split doesn't give everyone
        a lastname/surname of MD

    """

    if not name:
        return

    if name.upper().endswith(' MD'):
        re_name = name[:-3]
    else:
        return name

    return re_name


def address_split(address, addressType="Official"):
    """ Split a single line address to

        addressType:
        addressLine1
        addressLine2
        City
        state
        zip

        input sample1 = "1 BATES BLVD SUITE 100 ORINDA CA 945633309"
        input sample2 = "PO BOX 619092 ROSEVILLE CA 95661-9092"

    """

    if not address:
        return
    zip = zipcode_from_text(address)

    # split address on spaces.
    a = address.split(" ")
    # print("\nAddress is now:%s" % a)
    # work from back to front
    if zip:
        state = a[-2]
        city = a[-3]
        addressLine1 = ' '.join(a[:-3])
    else:
        state = a[-1]
        city = a[-2]
        addressLine1 = ' '.join(a[:-2])

    addr = {"addressType": addressType,
            "addressLine1": addressLine1,
            "city": city,
            "state": state,
            "zip": zip}

    # print("\nAddress dict is:%s" % addr)
    return addr


def zipcode_from_text(address):
    """ Get zip code from end of text string """

    postal_code = re.search('(\d{5})([- ])?(\d{4})?$', address)
    if postal_code is not None:
        # print("\nPostalCode:%s" % postal_code.group(0))
        return postal_code.group(0)

    return
