import json
import logging

from urllib.parse import urlencode
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from apps.fhir.bluebutton.utils import (request_call,
                                        FhirServerUrl,
                                        get_host_url,
                                        prepend_q,
                                        post_process_request,
                                        get_resource_names,
                                        get_resourcerouter,
                                        build_rewrite_list,
                                        get_response_text,
                                        build_oauth_resource)

from apps.fhir.bluebutton.xml_handler import (xml_to_dom,
                                              dom_conformance_filter,
                                              append_security)

from ..opoutcome_utils import (strip_format_for_back_end,
                               valid_interaction,
                               request_format)


logger = logging.getLogger('hhs_server.%s' % __name__)

__author__ = 'Mark Scrimshire:@ekivemark'


def oauth_fhir_conformance(request, via_oauth=True, *args, **kwargs):
    """ Pull and filter fhir Conformance statement

    BaseDstu2 = "Conformance"
    BaseStu3 = "CapabilityStatement"

    metadata call

    """
    return metadata(request, via_oauth=True, *args, **kwargs)


def fhir_conformance(request, via_oauth=False, *args, **kwargs):
    """ Pull and filter fhir Conformance statement

    BaseDstu2 = "Conformance"
    BaseStu3 = "CapabilityStatement"

    metadata call

    """

    return metadata(request, via_oauth=False, *args, **kwargs)


def metadata(request, via_oauth=False, *args, **kwargs):
    """
    Arrive here to do capabilityStatement or Conformance
    aka metadata

    oauth_fhir_conformance sets via_oauth=True
    fhir_conformance sets via_oauth=False

    :param request:
    :param via_oauth:
    :param args:
    :param kwargs:
    :return:
    """
    cx = None
    rr = get_resourcerouter()
    call_to = FhirServerUrl()

    if call_to.endswith('/'):
        call_to += 'metadata'
    else:
        call_to += '/metadata'

    pass_params = request.GET
    # pass_params should be an OrderedDict after strip_auth

    requested_format = request_format(pass_params)

    # now we simplify the format/_format request for the back-end
    pass_params = strip_format_for_back_end(pass_params)
    back_end_format = pass_params['_format']

    encoded_params = urlencode(pass_params)
    pass_params = prepend_q(encoded_params)

    r = request_call(request,
                     call_to + pass_params,
                     cx)

    text_out = ''
    host_path = get_host_url(request, '?')

    if r.status_code >= 300:
        logger.debug("We have an error code to deal with: %s" % r.status_code)
        return HttpResponse(json.dumps(r._content),
                            status=r.status_code,
                            content_type='application/json')

    rewrite_url_list = build_rewrite_list(cx)
    text_in = get_response_text(fhir_response=r)

    text_out = post_process_request(request,
                                    back_end_format,
                                    host_path,
                                    text_in,
                                    rewrite_url_list)

    if requested_format == "xml":
        xml_dom = xml_to_dom(text_out)

        text_out = dom_conformance_filter(xml_dom, rr)

        # Append Security to ConformanceStatement
        security_endpoint = build_oauth_resource(request, format_type="xml")
        text_out = append_security(text_out, security_endpoint)

        return HttpResponse(text_out, content_type='application/xml')
    else:
        od = conformance_filter(text_out, back_end_format, rr)

        # Append Security to ConformanceStatement
        security_endpoint = build_oauth_resource(request, format_type="json")
        od['rest'][0]['security'] = security_endpoint

        return JsonResponse(od)


def conformance_filter(text_block, fmt, rr=None):
    """ Filter FHIR Conformance Statement based on
        supported ResourceTypes
    """

    # Get a list of resource names
    if rr is None:
        rr = get_resourcerouter()

    resource_names = get_resource_names(rr)
    ct = 0
    if text_block:
        if 'rest' in text_block:
            for k in text_block['rest']:
                for i, v in k.items():
                    if i == 'resource':
                        supp_resources = get_supported_resources(v,
                                                                 resource_names,
                                                                 rr)
                        text_block['rest'][ct]['resource'] = supp_resources
                ct += 1
        else:
            text_block = ""
    else:
        text_block = ""

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
