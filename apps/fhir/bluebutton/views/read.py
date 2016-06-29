import json
import logging
import requests

from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from apps.fhir.core.utils import (error_status,
                                  kickout_403,
                                  write_session,
                                  find_ikey,
                                  get_search_param_format,
                                  get_target_url,
                                  ERROR_CODE_LIST,
                                  SESSION_KEY)

from apps.fhir.bluebutton.utils import (
    check_rt_controls,
    check_access_interaction_and_resource_type,
    masked_id,
    strip_oauth,
    build_params,
    FhirServerUrl,
    mask_list_with_host,
    get_host_url)

from apps.fhir.bluebutton.models import Crosswalk


logger = logging.getLogger('hhs_server.%s' % __name__)

DF_EXTRA_INFO = False


def read(request, resource_type, r_id, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    interaction_type = 'read'

    read_fhir = generic_read(request,
                             interaction_type,
                             resource_type,
                             r_id,
                             *args,
                             **kwargs)

    return read_fhir


def generic_read(request,
                 interaction_type,
                 resource_type,
                 r_id=None,
                 vid=None,
                 *args,
                 **kwargs):
    """
    Read from remote FHIR Server

    :param request:
    :param interaction_type:
    :param resource_type:
    :param id:
    :param vid:
    :param args:
    :param kwargs:
    :return:

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234

    """
    # interaction_type = 'read' or '_history' or 'vread' or 'search'
    # logger.debug('interaction_type: %s' % interaction_type)

    # Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type,
                                                      interaction_type)
    if deny:
        # if not allowed, return a 4xx error.
        return deny

    srtc = check_rt_controls(resource_type)
    # We get back a Supported ResourceType Control record or None

    # logger.debug('srtc: %s' % srtc)

    try:
        cx = Crosswalk.objects.get(user=request.user)
    except Crosswalk.DoesNotExist:
        cx = None
        # logger.debug('Crosswalk for %s does not exist' % request.user)

    if (cx is None and srtc is not None):
        # There is a srtc record so we need to check override_search
        if srtc.override_search:
            # If user is not in Crosswalk and srtc has search_override = True
            # We need to prevent search to avoid data leakage.
            return kickout_403('Error 403: %s Resource is access controlled.'
                               ' No records are linked to user:'
                               '%s' % (resource_type, request.user))

    # Request.user = user
    # interaction_type = read | _history | vread
    # resource_type = 'Patient | Practitioner | ExplanationOfBenefit ...'
    # id = fhir_id (potentially masked)
    # vid = Version Id

    # Check the resource_type to see if it has a url
    # Check the resource_type to see if masking is required
    # Get the FHIR_Server (from crosswalk via request.user)
    # if masked get the fhir_id from crosswalk
    # if search_override strip search items (search_block)
    # if search_override add search keys

    fhir_url = ''
    # get the default_url from ResourceTypeControl

    # Add default FHIR Server URL to re-write

    rewrite_url_list = settings.FHIR_SERVER_CONF['REWRITE_FROM']
    # print("Starting Rewrite_list:%s" % rewrite_url_list)

    if srtc:
        # logger.debug('SRTC:%s' % srtc)
        if srtc.default_url == '':
            fhir_url = FhirServerUrl() + resource_type + '/'
            if FhirServerUrl()[:-1] not in rewrite_url_list:
                rewrite_url_list.append(FhirServerUrl()[:-1])

        else:
            fhir_url = srtc.default_url + resource_type + '/'
            rewrite_url_list.append(srtc.default_url)
            # print('srtc.default_url')

    else:
        logger.debug('CX:%s' % cx)
        if cx:
            fhir_url = cx.get_fhir_resource_url(resource_type)
            rewrite_url_list.append(fhir_url.replace(resource_type + '/', ''))
        else:
            # logger.debug('FHIRServer:%s' % FhirServerUrl())
            fhir_url = FhirServerUrl() + resource_type + '/'
            if FhirServerUrl()[:-1] not in rewrite_url_list:
                rewrite_url_list.append(FhirServerUrl())

    # logger.debug('FHIR URL:%s' % fhir_url)
    # logger.debug('Rewrite List:%s' % rewrite_url_list)

    if interaction_type == 'search':
        key = None
    else:
        key = masked_id(resource_type, cx, srtc, r_id, slash=False)
        fhir_url += key + '/'

    ###########################

    # Now we get to process the API Call.

    # logger.debug('Now we need to evaluate the parameters and
    #              'arguments to work with %s and '
    #              '%s. GET parameters:%s' % (key,
    #                                         request.user,
    #                                         request.GET))

    # Internal handling format is json
    # Remove the oauth elements from the GET
    pass_params = strip_oauth(request.GET)

    if interaction_type == 'search':
        if cx is not None:
            r_id = cx.fhir_id

    pass_params = build_params(pass_params, srtc, r_id)

    if interaction_type == 'vread':
        pass_to = fhir_url + '_history' + '/' + vid
    elif interaction_type == '_history':
        pass_to = fhir_url + '_history'
    else:  # interaction_type == 'read':
        pass_to = fhir_url

    # logger.debug('Here is the URL to send, %s now add '
    #              'GET parameters %s' % (pass_to, pass_params))

    if pass_params is not '':
        pass_to += pass_params

    # print("Making request:", pass_to)
    # Now make the call to the backend API
    try:
        r = requests.get(pass_to)

    except requests.ConnectionError:
        # logger.debug('Problem connecting to FHIR Server')
        messages.error(request, 'FHIR Server is unreachable.')
        return HttpResponseRedirect(reverse_lazy('api:v1:home'))

    if r.status_code in ERROR_CODE_LIST:
        return error_status(r, r.status_code)

    text_out = ''
    # logger.debug('r:%s' % r.text)

    # if srtc is not None:
    #     # Replace the default_url
    #     if srtc.default_url:
    #         logger.debug('We will replace url srtc:%s' % srtc.default_url)
    #         if srtc.default_url not in rewrite_url_list:
    #             rewrite_url_list.append(srtc.default_url)
    #
    # if cx is not None:
    #     # replace the crosswalk fhir url
    #     if cx.fhir_source.fhir_url:
    #         logger.debug('we will replace cx:%s' % (cx.fhir_source.fhir_url))
    #         if cx.fhir_source.fhir_url not in rewrite_url_list:
    #             rewrite_url_list.append(cx.fhir_source.fhir_url)

    # logger.debug('Rewrite List:%s' % rewrite_url_list)

    host_path = get_host_url(request, resource_type)[:-1]
    # logger.debug('host path:%s' % host_path)

    # get 'xml' 'json' or ''
    fmt = get_search_param_format(pass_params)

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
        od['note'] = 'This is the %s Pass Thru (%s) ' % (resource_type, key)
        if settings.DEBUG:
            od['note'] += 'using: %s ' % (pass_to)

    od['bundle'] = text_out

    # write session variables if _getpages was found
    ikey = find_ikey(r.text)
    if ikey is not '':

        save_url = get_target_url(fhir_url, resource_type)
        # print("Store fhir_url:%s but only: %s" % (fhir_url,save_url))
        content = {
            'fhir_to': save_url,
            'rwrt_list': rewrite_url_list,
            'res_type': resource_type,
            'intn_type': interaction_type,
            'key': key,
            'vid': vid
        }
        sesn_var = write_session(request, ikey, content, skey=SESSION_KEY)
        if sesn_var:
            logger.debug("Problem writing session variables."
                         " Returned %s" % sesn_var)
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
