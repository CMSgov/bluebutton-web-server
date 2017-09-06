#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: home.py
Created: 6/27/16 3:24 PM

"""
import json
import logging

from collections import OrderedDict

try:
    # python2
    from urllib import urlencode
except ImportError:
    # python3
    from urllib.parse import urlencode

# from django.conf import settings

from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required

# from apps.fhir.bluebutton.models import ResourceTypeControl
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import (request_call,
                                        FhirServerUrl,
                                        get_host_url,
                                        strip_oauth,
                                        build_output_dict,
                                        prepend_q,
                                        post_process_request,
                                        pretty_json,
                                        conformance_or_capability,
                                        get_crosswalk,
                                        get_resource_names,
                                        get_resourcerouter,
                                        build_rewrite_list)

from apps.fhir.bluebutton.xml_handler import (xml_to_dom,
                                              dom_conformance_filter)
from apps.dot_ext.decorators import capability_protected_resource


from apps.fhir.fhir_core.utils import (read_session,
                                       get_search_param_format,
                                       strip_format_for_back_end,
                                       SESSION_KEY,
                                       ERROR_CODE_LIST,
                                       valid_interaction,
                                       build_querystring,
                                       request_format)

from apps.home.views import authenticated_home

logger = logging.getLogger('hhs_server.%s' % __name__)

__author__ = 'Mark Scrimshire:@ekivemark'


def fhir_search_home(request, via_oauth=False):
    """ Check if search parameters are in the GET

     if not pass through to authenticated_home

     """

    if request.user.is_authenticated():

        if request.method == 'GET':
            if '_getpages' in request.GET:
                # print("We got something to get")

                return rebuild_fhir_search(request, via_oauth)

    return authenticated_home(request)


def rebuild_fhir_search(request, via_oauth=False):
    """ Rebuild the Search String

    We will start to use a session variable

    We received:
    http://localhost:8000/cmsblue/fhir/v1
    ?_getpages=61c6e2d1-2b7c-49c3-a083-3d5b3874d4ff&_getpagesoffset=10
    &_count=10&_format=json&_pretty=true&_bundletype=searchset

    Session Variables will be storing:
    - FHIR Target URL/Resource
    - _getpages value
    - expires datetime

    Construct FHIR_Target_URL + search parameters

    """

    # now = str(datetime.now())
    ikey = ''
    if '_getpages' in request.GET:
        ikey = request.GET['_getpages']
        sn_vr = read_session(request, ikey, skey=SESSION_KEY)
        # logger.debug("Session info:%s" % sn_vr)

        if sn_vr == {}:
            # Nothing returned from Session Variables
            # Key could be expired or not matched
            return authenticated_home(request)

        url_call = sn_vr['fhir_to']
        url_call += '/?' + request.META['QUERY_STRING']

        rewrite_url_list = sn_vr['rwrt_list']
        resource_type = sn_vr['res_type']
        interaction_type = sn_vr['intn_type']
        key = sn_vr['key']
        vid = sn_vr['vid']

        if via_oauth:
            # get to user via resource_owner
            cx = get_crosswalk(request.resource_owner)
        else:
            # get user via logged in user
            cx = get_crosswalk(request.user)

        # logger.debug("Calling:%s" % url_call)
        r = request_call(request,
                         url_call,
                         cx,
                         reverse_lazy('authenticated_home'))

        host_path = get_host_url(request, '?')

        # get 'xml' 'json' or ''
        fmt = get_search_param_format(request.META['QUERY_STRING'])

        text_out = post_process_request(request,
                                        fmt,
                                        host_path,
                                        r.text,
                                        rewrite_url_list)
        od = build_output_dict(request,
                               OrderedDict(),
                               resource_type,
                               key,
                               vid,
                               interaction_type,
                               fmt,
                               text_out)

        if fmt == 'xml':
            # logger.debug('We got xml back in od')
            return HttpResponse(r.text, content_type='application/%s' % fmt)
            # return HttpResponse( tostring(dict_to_xml('content', od)),
            #                      content_type='application/%s' % fmt)
        elif fmt == 'json':
            # logger.debug('We got json back in od')
            return HttpResponse(pretty_json(od),
                                content_type='application/%s' % fmt)

        # logger.debug('We got a different format:%s' % fmt)
        return render(
            request,
            'bluebutton/default.html',
            {'content': pretty_json(od), 'output': od},
        )

    return authenticated_home(request)


@capability_protected_resource()
def oauth_fhir_conformance(request, via_oauth=True, *args, **kwargs):
    """ Pull and filter fhir Conformance statement

    BaseDstu2 = "Conformance"
    BaseStu3 = "CapabilityStatement"

    metadata call

    """
    if not request.user.is_authenticated():
        return authenticated_home(request)

    if via_oauth:
        # get user via resource_owner
        get_user = request.resource_owner
    else:
        get_user = request.user

    try:
        cx = Crosswalk.objects.get(user=get_user)
    except Crosswalk.DoesNotExist:
        cx = None
        # logger.debug('Crosswalk for %s does not exist' % request.user)

    if cx:
        rr = get_resourcerouter(cx)
        call_to = cx.fhir_source.fhir_url
    else:
        rr = get_resourcerouter()
        call_to = FhirServerUrl()

    resource_type = conformance_or_capability(call_to)

    if call_to.endswith('/'):
        call_to += 'metadata'
    else:
        call_to += '/metadata'

    pass_params = strip_oauth(request.GET)
    # pass_params should be an OrderedDict after strip_auth
    # logger.debug("result from strip_oauth:%s" % pass_params)

    # Let's store the inbound requested format
    # We need to simplify the format call to the backend
    # so that we get data we can manipulate
    requested_format = request_format(pass_params)

    # now we simplify the format/_format request for the back-end
    pass_params = strip_format_for_back_end(pass_params)
    back_end_format = pass_params['_format']

    encoded_params = urlencode(pass_params)
    #
    # Add ? to front of parameters if needed
    pass_params = prepend_q(encoded_params)

    # logger.debug("Calling:%s" % call_to + pass_params)

    ####################################################
    ####################################################

    r = request_call(request,
                     call_to + pass_params,
                     cx,
                     reverse_lazy('authenticated_home'))

    ####################################################
    ####################################################

    text_out = ''
    host_path = get_host_url(request, '?')

    # get 'xml' 'json' or ''
    # fmt = get_search_param_format(request.META['QUERY_STRING'])
    # force to json

    # logger.debug("Format:%s" % back_end_format)

    rewrite_url_list = build_rewrite_list(cx)
    # print("Starting Rewrite_list:%s" % rewrite_url_list)

    text_out = post_process_request(request,
                                    back_end_format,
                                    host_path,
                                    r.text,
                                    rewrite_url_list)

    query_string = build_querystring(request.GET.copy())
    # logger.debug("Query:%s" % query_string)

    if 'xml' in requested_format:
        # logger.debug('We got xml back in od')

        # logger.debug("is xml filtered?%s" % requested_format)
        xml_dom = xml_to_dom(text_out)
        text_out = dom_conformance_filter(xml_dom, rr)
        # logger.debug("Text from XML function:\n%s\n=========" % text_out)
        if 'html' not in requested_format:
            return HttpResponse(text_out,
                                content_type='application'
                                             '/%s' % requested_format)
        else:
            # logger.debug("Sending text_out for display: %s" % text_out[0:100])
            return render(
                request,
                'bluebutton/default_xml.html',
                {'output': text_out,
                 'content': {'parameters': query_string,
                             'resource_type': resource_type,
                             'request_method': "GET",
                             'interaction_type': "metadata",
                             'source': cx.fhir_source.name}})

            # return HttpResponse( tostring(dict_to_xml('content', od)),
        #                      content_type='application/%s' % fmt)
    elif back_end_format == 'json':
        # logger.debug('We got json back in od')
        od = conformance_filter(text_out, back_end_format, rr)
        text_out = pretty_json(od)
        if 'html' not in requested_format:
            return HttpResponse(text_out,
                                content_type='application/'
                                             '%s' % requested_format)
    else:
        # let's make sure we have json to deliver:
        od = conformance_filter(text_out, back_end_format, rr)
        text_out = pretty_json(od)

    # logger.debug('We got a different format:%s' % back_end_format)

    return render(
        request,
        'bluebutton/default.html',
        {'output': text_out,
         'content': {'parameters': query_string,
                     'resource_type': resource_type,
                     'request_method': "GET",
                     'interaction_type': "metadata",
                     'source': cx.fhir_source.name}})


@login_required()
def fhir_conformance(request, via_oauth=False, *args, **kwargs):
    """ Pull and filter fhir Conformance statement

    BaseDstu2 = "Conformance"
    BaseStu3 = "CapabilityStatement"

    metadata call

    """
    if not request.user.is_authenticated():
        return authenticated_home(request)

    if via_oauth:
        # get user via resource_owner
        get_user = request.resource_owner
    else:
        get_user = request.user

    try:
        cx = Crosswalk.objects.get(user=get_user)
    except Crosswalk.DoesNotExist:
        cx = None
        # logger.debug('Crosswalk for %s does not exist' % request.user)

    if cx:
        rr = get_resourcerouter(cx)
        call_to = cx.fhir_source.fhir_url
    else:
        rr = get_resourcerouter()
        call_to = FhirServerUrl()

    resource_type = conformance_or_capability(call_to)

    if call_to.endswith('/'):
        call_to += 'metadata'
    else:
        call_to += '/metadata'

    pass_params = strip_oauth(request.GET)
    # pass_params should be an OrderedDict after strip_auth
    # logger.debug("result from strip_oauth:%s" % pass_params)

    # Let's store the inbound requested format
    # We need to simplify the format call to the backend
    # so that we get data we can manipulate
    requested_format = request_format(pass_params)

    # now we simplify the format/_format request for the back-end
    pass_params = strip_format_for_back_end(pass_params)
    back_end_format = pass_params['_format']

    encoded_params = urlencode(pass_params)
    #
    # Add ? to front of parameters if needed
    pass_params = prepend_q(encoded_params)

    # logger.debug("Calling:%s" % call_to + pass_params)

    query_string = build_querystring(request.GET.copy())

    ####################################################
    ####################################################

    r = request_call(request,
                     call_to + pass_params,
                     cx,
                     reverse_lazy('authenticated_home'))

    ####################################################
    ####################################################

    text_out = ''
    host_path = get_host_url(request, '?')

    if r.status_code in ERROR_CODE_LIST:
        logger.debug("We have an error code to deal with: %s" % r.status_code)
        if 'html' in requested_format.lower():
            return render(
                request,
                'bluebutton/default.html',
                {'output': pretty_json(r._content, indent=4),
                 'fhir_id': cx.fhir_id,
                 'content': {'parameters': query_string,
                             'resource_type': resource_type,
                             'id': id,
                             'request_method': "GET",
                             'interaction_type': "search",
                             'div_texts': "",
                             'source': cx.fhir_source.name}})
        else:
            return HttpResponse(json.dumps(r._content, indent=4),
                                status=r.status_code,
                                content_type='application/json')

    # get 'xml' 'json' or ''
    # fmt = get_search_param_format(request.META['QUERY_STRING'])
    # force to json

    # logger.debug("Format:%s" % back_end_format)

    rewrite_url_list = build_rewrite_list(cx)
    # print("Starting Rewrite_list:%s" % rewrite_url_list)

    text_out = post_process_request(request,
                                    back_end_format,
                                    host_path,
                                    r.text,
                                    rewrite_url_list)
    # define query string further up before request_call
    # query_string = build_querystring(request.GET.copy())

    # logger.debug("Query:%s" % query_string)

    if 'xml' in requested_format:
        # logger.debug('We got xml back in od')

        # logger.debug("is xml filtered?%s" % requested_format)
        xml_dom = xml_to_dom(text_out)
        text_out = dom_conformance_filter(xml_dom, rr)
        # logger.debug("Text from XML function:\n%s\n=========" % text_out)
        if 'html' not in requested_format:
            return HttpResponse(text_out,
                                content_type='application'
                                             '/%s' % requested_format)
        else:
            # logger.debug("Sending text_out for display: %s" % text_out[0:100])
            return render(
                request,
                'bluebutton/default_xml.html',
                {'output': text_out,
                 'content': {'parameters': query_string,
                             'resource_type': resource_type,
                             'request_method': "GET",
                             'interaction_type': "metadata",
                             'source': cx.fhir_source.name}})

            # return HttpResponse( tostring(dict_to_xml('content', od)),
        #                      content_type='application/%s' % fmt)
    elif back_end_format == 'json':
        # logger.debug('We got json back in od')
        od = conformance_filter(text_out, back_end_format, rr)
        text_out = pretty_json(od)
        if 'html' not in requested_format:
            return HttpResponse(text_out,
                                content_type='application/'
                                             '%s' % requested_format)
    else:
        # let's make sure we have json to deliver:
        od = conformance_filter(text_out, back_end_format, rr)
        text_out = pretty_json(od)

    # logger.debug('We got a different format:%s' % back_end_format)

    return render(
        request,
        'bluebutton/default.html',
        {'output': text_out,
         'content': {'parameters': query_string,
                     'resource_type': resource_type,
                     'request_method': "GET",
                     'interaction_type': "metadata",
                     'source': cx.fhir_source.name}})


def conformance_filter(text_block, fmt, rr=None):
    """ Filter FHIR Conformance Statement based on
        supported ResourceTypes
    """
    # if fmt == "xml":
    #     # First attempt at xml filtering
    #     # logger.debug("xml block as text:\n%s" % text_block)
    #
    #     xml_dict = xml_to_dict(text_block)
    #     # logger.debug("xml dict:\n%s" % xml_dict)
    #     return xml_dict

    # Get a list of resource names
    if rr is None:
        rr = get_resourcerouter()

    resource_names = get_resource_names(rr)
    ct = 0

    for k in text_block['rest']:
        for i, v in k.items():
            if i == 'resource':
                supported_resources = get_supported_resources(v,
                                                              resource_names,
                                                              rr)
                text_block['rest'][ct]['resource'] = supported_resources
        ct += 1

    return text_block


def get_supported_resources(resources, resource_names, rr=None):
    """ Filter resources for resource type matches """

    if rr is None:
        rr = get_resourcerouter()

    resource_list = []
    # if resource 'type in resource_names add resource to resource_list
    for item in resources:
        for k, v in item.items():
            if k == 'type':
                if v in resource_names:
                    filtered_item = get_interactions(v, item, rr)
                    # logger.debug("Filtered Item:%s" % filtered_item)

                    resource_list.append(filtered_item)
                else:
                    pass
                    # print('\nDisposing of %s' % v)
            else:
                pass

    return resource_list


def get_interactions(resource, item, rr=None):
    """ filter interactions within an approved resource

    interaction":[{"code":"read"},
                  {"code":"vread"},
                  {"code":"update"},
                  {"code":"delete"},
                  {"code":"history-instance"},
                  {"code":"history-type"},
                  {"code":"create"},
                  {"code":"search-type"}
    """

    # DONE: Add rr to call
    if rr is None:
        rr = get_resourcerouter()

    valid_interactions = valid_interaction(resource, rr)
    permitted_interactions = []

    # Now we have a resource let's filter the interactions
    for k, v in item.items():
        if k == 'interaction':
            # We have a list of codes for interactions.
            # We have to filter them
            for action in v:
                # OrderedDict item with ('code', 'interaction')
                if action['code'] in valid_interactions:
                    permitted_interactions.append(action)

    # Now we can replace item['interaction']
    item['interaction'] = permitted_interactions

    return item
