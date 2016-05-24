#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: apps.fhir.bluebutton.utils
Created: 5/19/16 12:35 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import json
import logging
import time

try:
    # python2
    from urllib import urlencode
except ImportError:
    # python3
    from urllib.parse import urlencode

from collections import (OrderedDict,
                         defaultdict)

from django.conf import settings

from apps.fhir.core.utils import (kickout_404, kickout_403)
from apps.fhir.server.models import SupportedResourceType
from apps.fhir.bluebutton.models import ResourceTypeControl

FORMAT_OPTIONS_CHOICES = ['json', 'xml']

logger = logging.getLogger('hhs_server.%s' % __name__)


def notNone(value=None, default=None):
    """
    Test value. Return Default if None
    http://stackoverflow.com/questions/4978738/
    is-there-a-python-equivalent-of-the-c-sharp-null-coalescing-operator
    """
    if value is None:
        return default
    else:
        return value


def strip_oauth(get):
    """ Remove OAuth values from URL Parameters being sent to backend """

    # access_token can be passed in as a part of OAuth protected request.
    # as can: state=random_state_string&response_type=code&client_id=ABCDEF
    # Remove them before passing url through to FHIR Server

    strip_parms = ['access_token', 'state', 'response_type', 'client_id']

    logger.debug("Removing:%s from: %s" % (strip_parms, get))

    strip_oauth = get_url_query_string(get, strip_parms)

    logger.debug("resulting url parameters:%s" % strip_oauth)

    return strip_oauth


def block_params(get, srtc):
    """ strip parameters from search string """

    # Get parameters
    # split on &
    # get srtc.search_block as list
    if get:
        # set search_params to what is received as a default
        search_params = get
    else:
        # No get parameters to process so return
        search_params = ""
        return search_params

    # Now we need to see if there are any get parameters to remove
    if srtc:
        if srtc.override_search:
            search_params = get_url_query_string(get, srtc.get_search_block())

    return search_params


def add_params(srtc, key):
    """ Add filtering parameters to search string """

    # srtc.get_search_add will return a list
    # this will be in form "Patient={Value}"
    # Replaceable parameters can be included
    # Currently Supported Replaceable Parameters are:
    # %PATIENT% = key
    # modify this function to add more Replaceable Parameters

    # add_params = ""
    add_params = OrderedDict()

    if srtc:
        if srtc.override_search:
            params_list = srtc.get_search_add()

            logger.debug("Parameters to add:%s" % params_list)

            for item in params_list:
                # Run through list and do variable replacement
                if "%PATIENT%" in item:
                    item.replace('%PATIENT%', key)

            add_params = params_list

            logger.debug("Resulting additional parameters:%s" % add_params)

    return add_params


def concat_parms(front_part={}, back_part={}):
    """ Concatenate the Query Parameters Strings
        The strings should be urlencoded.

    """

    joined_parms = OrderedDict()

    logger.debug("Joining %s with: %s" % (front_part, back_part))
    if len(front_part) > 0:
        for k, v in front_part.items():
            # append front items
            joined_parms[k] = v

    if len(back_part) > 0:
        for k, v in back_part.items():
            # append back items
            joined_parms[k] = v

    concat_parms = "?" + urlencode(joined_parms)

    logger.debug("resulting string:%s" % concat_parms)

    # We have to do something
    # joined_parms = "?"
    #
    # if len(front_part) != 0:
    #     joined_parms += front_part
    #
    # if len(back_part) == 0:
    #     # nothing to add
    #     return joined_parms
    # else:
    #     joined_parms += "&" + back_part

    return concat_parms


def build_params(get, srtc, key ):
    """
    Build the URL Parameters.
    We have to skip any in the skip list.

    :param get:
    :return:
    """
    # We will default to json for content handling
    in_fmt = "json"
    pass_to = ""

    # First we strip the parameters that need to be blocked
    url_param = block_params(get, srtc)

    # Now we need to construct the parameters we need to add
    add_param = add_params(srtc, key)

    # Put the parameters together in urlencoded string
    # leading ? and parameters joined by &
    all_param = concat_parms(url_param, add_param)

    logger.debug("Parameter (post block/add):%s" % all_param)

    # now we check for _format being specified. Otherwise we get back html
    # by default we will process json unless _format is already set.

    all_param = add_format(all_param)

    logger.debug("add_Format returned:%s" % all_param)

    return all_param


def add_format(all_param=""):
    """ Check for _format in parameters and add if missing """

    if "_format" in all_param:
        # We have a _format setting.
        # Let's check for xml or json.
        if "_format=json" in all_param.lower():
            return all_param
        elif "_format=xml" in all_param.lower():
            return all_param

    # no _format set.
    # Let's set _format=json.
    if all_param != "":
        all_param += "&"
    else:
        all_param = "?"

    all_param += "_format=json"

    return all_param


def get_format(in_get):
    """
    Receive request.GET and check for _format
    if json or xml return .lower()
    if none return "json"
    :param in_get:
    :return: "json" or "xml"
    """
    got_get = get_to_lower(in_get)

    # set default to return
    result = ""

    if "_format" in got_get:
        # we have something to process

        # if settings.DEBUG:
        #    print("In Get:",in_get)
        fmt = got_get.get('_format','').lower()

        # if settings.DEBUG:
        #    print("Format Returned:", fmt)

        # Check for a valid lower case value
        if fmt in FORMAT_OPTIONS_CHOICES:
            result = fmt
        else:
            pass
            # if settings.DEBUG:
            #    print("No Match with Format Options:", fmt)

    return result


def get_to_lower(in_get):
    """
    Force the GET parameter keys to lower case
    :param in_get:
    :return:
    """

    if not in_get:
        # if settings.DEBUG:
        #    print("get_to_lower: Nothing to process")
        return in_get

    got_get = OrderedDict()
    # Deal with capitalization in request.GET.
    # force to lower
    for value in in_get:

        got_get[value.lower()] = in_get.get(value,"")
        # if settings.DEBUG:
        #     print("Got key", value.lower(), ":", got_get[value.lower()] )

    # if settings.DEBUG:
    #    print("Returning lowercase request.GET", got_get)

    return got_get


def get_url_query_string(get, skip_parm=[]):
    """
    Receive the request.GET Query Dict
    Evaluate against skip_parm by skipping any entries in skip_parm
    Return a query string ready to pass to a REST API.
    http://hl7-fhir.github.io/search.html#all

    # We need to force the key to lower case and skip params should be
    # lower case too

    eg. _lastUpdated=>2010-10-01&_tag=http://acme.org/codes|needs-review

    :param get: {}
    :param skip_parm: []
    :return: Query_String (QS)
    """
    logger.debug("Evaluating: %s to remove:%s" % (get,skip_parm))

    filtered_dict = OrderedDict()

    # Check we got a get dict
    if not get:
        return filtered_dict

    # Now we work through the parameters

    for k, v in get.items():

        logger.debug("K/V: [%s/%s]" % (k,v))

        if k in skip_parm:
            pass
        else:
            # Build the query_string
            filtered_dict[k] = v

    # qs = urlencode(filtered_dict)
    qs = filtered_dict

    logger.debug("Filtered parameters:%s from:%s" % (qs, filtered_dict))
    return qs


def FhirServerUrl(server=None,path=None, release=None ):
    # fhir_server_configuration = {"SERVER":"http://fhir-test.bbonfhir.com:8081",
    #                              "PATH":"",
    #                              "RELEASE":"/baseDstu2"}
    # FHIR_SERVER_CONF = fhir_server_configuration
    # FHIR_SERVER = FHIR_SERVER_CONF['SERVER'] + FHIR_SERVER_CONF['PATH']

    fhir_server = notNone(server, settings.FHIR_SERVER_CONF['SERVER'])

    fhir_path = notNone(path, settings.FHIR_SERVER_CONF['PATH'])

    fhir_release = notNone(release, settings.FHIR_SERVER_CONF['RELEASE'])

    if not fhir_release.endswith('/'):
        fhir_release += "/"

    return fhir_server + fhir_path + fhir_release


def check_access_interaction_and_resource_type(resource_type, interaction_type):
    try:
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        if interaction_type not in rt.get_supported_interaction_types():
            msg = "The interaction: %s is not permitted on %s FHIR " \
                  "resources on this FHIR sever." % (interaction_type,
                                                     resource_type)
            return kickout_403(msg)
    except SupportedResourceType.DoesNotExist:
        msg = "%s is not a supported resource type on this FHIR server." % resource_type
        return kickout_404(msg)

    return False


def check_rt_controls(resource_type):
    # Check for controls to apply to this resource_type
    logger.debug("Resource_Type =%s" % resource_type)

    rt = SupportedResourceType.objects.get(resource_name=resource_type)

    logger.debug("Working with SupportedResourceType:%s" % rt)

    try:
        srtc = ResourceTypeControl.objects.get(resource_name=rt)
    except ResourceTypeControl.DoesNotExist:
        srtc = None
        # srtc = {}
        # srtc['empty'] = True
        # srtc['resource_name'] = ""
        # srtc['override_url_id'] = False
        # srtc['override_search'] = False
        # srtc['search_block'] = ['',]
        # srtc['search_add'] = ['',]
        # srtc['group_allow'] = ""
        # srtc['group_exclude'] = ""
        # srtc['default_url'] = ""

    return srtc


def masked(srtc):
    """ check if force_url_override is set in SupportedResourceType """


    mask = False
    if srtc:
        if srtc.override_url_id:
            mask = True

    return mask


def masked_id(crosswalk, srtc, resource_type, orig_id, slash=True):
    """ Get the correct id
     if crosswalk.fhir_source.shard_by == resource_type

     """
    id = orig_id
    if srtc:
        if srtc.override_url_id:
            if crosswalk:
                if resource_type.lower() == crosswalk.fhir_source.shard_by.lower():
                    logger.debug("Replacing %s with %s" % (id, crosswalk.fhir_id))
                    id = crosswalk.fhir_id

    if slash:
        id += "/"

    return id


