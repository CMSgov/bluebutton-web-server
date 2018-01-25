from django.http import HttpResponse, JsonResponse
import json
import logging

from apps.dot_ext.decorators import require_valid_token
from apps.fhir.bluebutton.utils import (request_get_with_parms,
                                        block_params,
                                        build_rewrite_list,
                                        check_access_interaction_and_resource_type,
                                        check_rt_controls,
                                        get_crosswalk,
                                        get_fhir_id,
                                        get_host_url,
                                        get_resourcerouter,
                                        post_process_request,
                                        get_response_text)

from apps.fhir.server.utils import (search_add_to_list,
                                    payload_additions,
                                    payload_var_replace)

from ..opoutcome_utils import (kickout_403,
                               kickout_404)


logger = logging.getLogger('hhs_server.%s' % __name__)


@require_valid_token()
def search(request, resource_type, *args, **kwargs):
    """
    Search from Remote FHIR Server
    """

    logger.debug("resource_type: %s" % resource_type)
    logger.debug("Interaction: search. ")
    logger.debug("Request.path: %s" % request.path)

    crosswalk = get_crosswalk(request.resource_owner)

    resource_router = get_resourcerouter(crosswalk)

    # Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type, 'search', resource_router)

    if deny:
        return deny

    supported_resource_type_control = check_rt_controls(resource_type, resource_router)

    if supported_resource_type_control is None:
        return kickout_404('Unsupported ResourceType')

    if (crosswalk is None and supported_resource_type_control is not None):
        if supported_resource_type_control.override_search:
            return kickout_403('Error 403: %s Resource is access controlled.'
                               ' No records are linked to user:'
                               '%s' % (resource_type, request.user))

    target_url = resource_router.fhir_url + supported_resource_type_control.resourceType + "/"

    # Analyze the _format parameter
    # Sve the display _format

    # request.GET is immutable so take a copy to allow the values to be edited.
    payload = {}

    # Get payload with oauth parameters removed
    # Add the format for back-end
    payload['_format'] = 'application/json+fhir'

    payload = block_params(payload, supported_resource_type_control)

    patient_id = '' if resource_type.lower() == 'patient' else get_fhir_id(crosswalk)

    params_list = search_add_to_list(supported_resource_type_control.search_add)

    payload = payload_additions(payload, params_list)

    if resource_type.lower() == 'patient':
        logger.debug("Working resource:%s" % resource_type)
        logger.debug("Working payload:%s" % payload)

        payload['_id'] = patient_id
        if 'patient' in payload:
            del payload['patient']

    for pyld_k, pyld_v in payload.items():
        if pyld_v is None:
            pass
        elif '%PATIENT%' in pyld_v:
            payload = payload_var_replace(payload,
                                          pyld_k,
                                          new_value=patient_id,
                                          old_value='%PATIENT%')

    # add the _format setting
    payload['_format'] = 'application/json+fhir'

    # Make the request_call
    r = request_get_with_parms(request,
                               target_url,
                               json.loads(json.dumps(payload)),
                               crosswalk,
                               timeout=resource_router.wait_time)

    if r.status_code >= 300:
        logger.debug("We have an error code to deal with: %s" % r.status_code)
        return HttpResponse(json.dumps(r._content),
                            status=r.status_code,
                            content_type='application/json')

    rewrite_list = build_rewrite_list(crosswalk)
    host_path = get_host_url(request, resource_type)[:-1]

    text_in = get_response_text(fhir_response=r)

    text_out = post_process_request(request,
                                    host_path,
                                    text_in,
                                    rewrite_list)

    return JsonResponse(text_out)
