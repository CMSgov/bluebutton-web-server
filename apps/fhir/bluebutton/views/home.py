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
import requests

from collections import OrderedDict

try:
    # python2
    from urllib import urlencode
except ImportError:
    # python3
    from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy

from django.shortcuts import render, HttpResponseRedirect, HttpResponse

# from apps.fhir.bluebutton.models import ResourceTypeControl
from apps.fhir.server.models import SupportedResourceType
from apps.fhir.bluebutton.utils import (get_host_url,
                                        mask_list_with_host,
                                        strip_oauth,
                                        pretty_json)

from apps.fhir.core.utils import (error_status,
                                  read_session,
                                  get_search_param_format,
                                  ERROR_CODE_LIST,
                                  SESSION_KEY)

from apps.home.views import authenticated_home

logger = logging.getLogger('hhs_server.%s' % __name__)

__author__ = 'Mark Scrimshire:@ekivemark'

DF_EXTRA_INFO = False


def fhir_search_home(request):
    """ Check if search parameters are in the GET

     if not pass through to authenticated_home

     """

    if request.user.is_authenticated():

        if request.method == 'GET':
            if '_getpages' in request.GET:
                # print("We got something to get")

                return rebuild_fhir_search(request)

    return authenticated_home(request)


def rebuild_fhir_search(request):
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

        logger.debug("Calling:%s" % url_call)
        try:
            r = requests.get(url_call)
        except requests.ConnectionError:
            # logger.debug('Problem connecting to FHIR Server')
            messages.error(request, 'FHIR Server is unreachable.')
            return HttpResponseRedirect(reverse_lazy('authenticated_home'))

        if r.status_code in ERROR_CODE_LIST:
            return error_status(r, r.status_code)

        text_out = ''
        host_path = get_host_url(request, '?')

        # get 'xml' 'json' or ''
        fmt = get_search_param_format(request.META['QUERY_STRING'])

        if fmt == 'xml':
            # We will add xml support later

            text_out = mask_list_with_host(request,
                                           host_path,
                                           r.text,
                                           rewrite_url_list)
            # text_out= minidom.parseString(text_out).toprettyxml()
        else:
            # dealing with json
            # text_out = r.json()
            pre_text = mask_list_with_host(request,
                                           host_path,
                                           r.text,
                                           rewrite_url_list)
            text_out = json.loads(pre_text, object_pairs_hook=OrderedDict)

        od = OrderedDict()
        od['resource_type'] = resource_type
        od['id'] = key
        if vid is not None:
            od['vid'] = vid

        # logger.debug('Query List:%s' % request.META['QUERY_STRING'])

        if DF_EXTRA_INFO:
            od['request_method'] = request.method
            od['interaction_type'] = interaction_type
            od['parameters'] = request.GET.urlencode()
            # logger.debug('or:%s' % od['parameters'])
            od['format'] = fmt
            od['note'] = 'This is the %s Pass Thru ' \
                         '(%s) ' % (resource_type, key)

        od['bundle'] = text_out

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
            'cmsblue/default.html',
            {'content': pretty_json(od), 'output': od},
        )

    return authenticated_home(request)


def fhir_conformance(request, *args, **kwargs):
    """ Pull and filter fhir Conformance statement

    metadata call

    """
    if not request.user.is_authenticated():
        return authenticated_home(request)

    resource_type = 'Conformance'
    call_to = settings.FHIR_SERVER_CONF['SERVER']
    call_to += settings.FHIR_SERVER_CONF['PATH']
    call_to += settings.FHIR_SERVER_CONF['RELEASE']
    call_to += '/metadata'

    pass_params = urlencode(strip_oauth(request.GET))
    if len(pass_params) > 0:
        pass_params = '?' + pass_params
    # print("Parameters:", pass_params)
    logger.debug("Calling:%s" % call_to + pass_params)
    try:
        r = requests.get(call_to + pass_params)
    except requests.ConnectionError:
        # logger.debug('Problem connecting to FHIR Server')
        messages.error(request, 'FHIR Server is unreachable.')
        return HttpResponseRedirect(reverse_lazy('authenticated_home'))

    if r.status_code in ERROR_CODE_LIST:
        return error_status(r, r.status_code)

    text_out = ''
    host_path = get_host_url(request, '?')

    # get 'xml' 'json' or ''
    fmt = get_search_param_format(request.META['QUERY_STRING'])

    rewrite_url_list = settings.FHIR_SERVER_CONF['REWRITE_FROM']
    # print("Starting Rewrite_list:%s" % rewrite_url_list)

    od = {}

    if fmt == 'xml':
        # We will add xml support later

        text_out = mask_list_with_host(request,
                                       host_path,
                                       r.text,
                                       rewrite_url_list)
        # text_out= minidom.parseString(text_out).toprettyxml()
    else:
        # dealing with json
        # text_out = r.json()
        pre_text = mask_list_with_host(request,
                                       host_path,
                                       r.text,
                                       rewrite_url_list)
        text_out = json.loads(pre_text, object_pairs_hook=OrderedDict)

        od = conformance_filter(text_out)

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
        {'output': pretty_json(od),
         'content': {'parameters': request.GET.urlencode(),
                     'resource_type': resource_type,
                     'request_method': "GET",
                     'interaction_type': "metadata"}})


def conformance_filter(text_block):
    """ Filter FHIR Conformance Statement based on
        supported ResourceTypes
    """

    # Get a list of resource names
    resource_names = get_resource_names()
    ct = 0
    for k in text_block['rest']:
        for i, v in k.items():
            if i == 'resource':
                supported_resources = get_supported_resources(v,
                                                              resource_names)
                text_block['rest'][ct]['resource'] = supported_resources
        ct += 1

    return text_block


def get_resource_names():
    """ Get names for all approved resources """

    all_resources = SupportedResourceType.objects.all()
    resource_names = []
    for name in all_resources:
        # Get the resource names into a list
        resource_names.append(name.resource_name)

    return resource_names


def get_supported_resources(resources, resource_names):
    """ Filter resources for resource type matches """

    resource_list = []
    # if resource 'type in resource_names add resource to resource_list
    for item in resources:
        for k, v in item.items():
            if k == 'type':
                if v in resource_names:
                    filtered_item = get_interactions(v, item)
                    logger.debug("Filtered Item:%s" % filtered_item)
                    resource_list.append(item)
                else:
                    pass
                    # print('\nDisposing of %s' % v)
            else:
                pass

    # print("\nSupported Resources:",
    #       pretty_json(resource_list))

    return resource_list


def get_interactions(resource, item):
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

    valid_interactions = valid_interaction(resource)
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


def valid_interaction(resource):
    """ Create a list of Interactions for the resource """

    interaction_list = []
    try:
        resource_interaction = \
            SupportedResourceType.objects.get(resource_name=resource)
    except SupportedResourceType.DoesNotExist:
        # this is a strange error
        # earlier gets should have found a record
        # otherwise we wouldn't get in to this function
        # so we will return an empty list.
        return interaction_list

    # Now we can build the interaction_list
    if resource_interaction.get:
        interaction_list.append("get")
    if resource_interaction.put:
        interaction_list.append("put")
    if resource_interaction.create:
        interaction_list.append("create")
    if resource_interaction.read:
        interaction_list.append("read")
    if resource_interaction.vread:
        interaction_list.append("vread")
    if resource_interaction.update:
        interaction_list.append("update")
    if resource_interaction.delete:
        interaction_list.append("delete")
    if resource_interaction.search:
        interaction_list.append("search-type")
    if resource_interaction.history:
        interaction_list.append("history-instance")
        interaction_list.append("history-type")

    return interaction_list
