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
from datetime import datetime
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

from apps.fhir.bluebutton.utils import (get_host_url,
                                        mask_list_with_host,
                                        strip_oauth)

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
    http://localhost:8000/bluebutton/fhir/v1
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
            return HttpResponse(json.dumps(od, indent=4),
                                content_type='application/%s' % fmt)

        # logger.debug('We got a different format:%s' % fmt)
        return render(
            request,
            'bluebutton/default.html',
            {'content': json.dumps(od, indent=4), 'output': od},
        )

    return authenticated_home(request)


def fhir_conformance(request, *args, **kwargs):
    """ Pull and filter fhir Conformance statement

    metadata call

    """
    if request.user.is_authenticated():
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

        od = text_out

        if fmt == 'xml':
            # logger.debug('We got xml back in od')
            return HttpResponse(r.text, content_type='application/%s' % fmt)
            # return HttpResponse( tostring(dict_to_xml('content', od)),
            #                      content_type='application/%s' % fmt)
        elif fmt == 'json':
            # logger.debug('We got json back in od')
            return HttpResponse(json.dumps(od, indent=4),
                                content_type='application/%s' % fmt)

        # logger.debug('We got a different format:%s' % fmt)


        return render(
            request,
            'bluebutton/default.html',
            {'output': json.dumps(od, indent=4),
             'content': {'parameters': request.GET.urlencode(),
                         'resource_type': 'Conformance',
                         'request_method': "GET",
                         'interaction_type': "metadata"}})

    else:
        return authenticated_home(request)
