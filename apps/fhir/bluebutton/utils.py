import os
import json
import logging
import pytz
import requests
import uuid

from collections import OrderedDict
from datetime import datetime
from pytz import timezone

from django.conf import settings
from django.contrib import messages
from .opoutcome_utils import (kickout_403,
                              kickout_404)
from apps.fhir.server.models import (SupportedResourceType,
                                     ResourceRouter)

from oauth2_provider.models import AccessToken

from apps.wellknown.views import (base_issuer, build_endpoint_info)
from .models import Crosswalk, Fhir_Response

logger = logging.getLogger('hhs_server.%s' % __name__)
logger_error = logging.getLogger('hhs_server_error.%s' % __name__)
logger_debug = logging.getLogger('hhs_server_debug.%s' % __name__)
logger_info = logging.getLogger('hhs_server_info.%s' % __name__)


def get_user_from_request(request):
    """Returns a user or None with login or OAuth2 API"""
    user = None
    if hasattr(request, 'resource_owner'):
        user = request.resource_owner
    if hasattr(request, 'user'):
        if not request.user.is_anonymous():
            user = request.user
    return user


def get_ip_from_request(request):

    """Returns the IP of the request, accounting for the possibility of being
    behind a proxy.
    """
    ip = request.META.get("HTTP_X_FORWARDED_FOR", None)
    if ip:
        # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
        ip = ip.split(", ")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip


def get_access_token_from_request(request):
    """Returns a user or None with login or OAuth2 API"""
    token = ""
    if hasattr(request, 'resource_owner'):
        if 'HTTP_AUTHORIZATION' in request.META:
            bearer, token = request.META['HTTP_AUTHORIZATION'].split(' ')
        if 'Authorization' in request.META:
            bearer, token = request.META['Authorization'].split(' ')
    return token


def get_fhir_now(my_now=None):
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


def get_timestamp(request):
    """ hhs_oauth_server.request_logging.RequestTimeLoggingMiddleware
        adds request._logging_start_dt

        we grab it or set a timestamp and return it.

    """

    if not hasattr(request, '_logging_start_dt'):
        return datetime.now(pytz.utc).isoformat()

    else:
        return request._logging_start_dt


def get_query_id(request):
    """ hhs_oauth_server.request_logging.RequestTimeLoggingMiddleware
        adds request._logging_uuid

        we grab it or set a uuid and return it.

    """
    if not hasattr(request, '_logging_uuid'):
        return uuid.uuid1()

    else:
        return request._logging_uuid


def get_query_counter(request):
    """ hhs_oauth_server.request_logging.RequestTimeLoggingMiddleware
        adds request._logging_pass

        we grab it or set a counter and return it.

    """
    if not hasattr(request, '_logging_pass'):
        return 1

    else:
        return request._logging_pass


def generate_info_headers(request):
    """Returns a dict of headers to be sent to the backend"""
    result = {}
    # get timestamp from request via Middleware, or get current time
    result['BlueButton-OriginalQueryTimestamp'] = str(get_timestamp(request))

    # get uuid or set one
    result['BlueButton-OriginalQueryId'] = str(get_query_id(request))

    # get query counter or set to 1
    result['BlueButton-OriginalQueryCounter'] = str(get_query_counter(request))

    # Return resource_owner or user
    user = get_user_from_request(request)
    originating_ip = get_ip_from_request(request)
    cx = get_crosswalk(user)
    if cx:
        # we need to send the HicnHash or the fhir_id
        if len(cx.fhir_id) > 0:
            result['BlueButton-BeneficiaryId'] = 'patientId:' + str(cx.fhir_id)
        else:
            result['BlueButton-BeneficiaryId'] = 'hicnHash:' + str(cx.user_id_hash)
    else:
        # Set to empty
        result['BlueButton-BeneficiaryId'] = ""

    if user:
        result['BlueButton-UserId'] = str(user.id)
        result['BlueButton-User'] = str(user)
        result['BlueButton-Application'] = ""
        result['BlueButton-ApplicationId'] = ""
        if AccessToken.objects.filter(token=get_access_token_from_request(request)).exists():
            at = AccessToken.objects.get(token=get_access_token_from_request(request))
            result['BlueButton-Application'] = str(at.application.name)
            result['BlueButton-ApplicationId'] = str(at.application.id)
            result['BlueButton-DeveloperId'] = str(at.application.user.id)
            result['BlueButton-Developer'] = str(at.application.user)
        else:
            result['BlueButton-Application'] = ""
            result['BlueButton-ApplicationId'] = ""
            result['BlueButton-DeveloperId'] = ""
            result['BlueButton-Developer'] = ""

    if originating_ip:
        result['BlueButton-OriginatingIpAddress'] = originating_ip
    else:
        result['BlueButton-OriginatingIpAddress'] = ""

    return result


def request_call(request, call_url, cx=None, timeout=None):
    """  call to request or redirect on fail
    call_url = target server URL and search parameters to be sent
    cx = Crosswalk record. The crosswalk is keyed off Request.user
    timeout allows a timeout in seconds to be set.

    FhirServer is joined to Crosswalk.
    FhirServerAuth and FhirServerVerify receive cx and lookup
       values in the linked fhir_server model.

    """

    # Updated to receive cx (Crosswalk entry for user)
    # call FhirServer_Auth(cx) to get authentication
    auth_state = FhirServerAuth(cx)

    verify_state = FhirServerVerify(cx)
    if auth_state['client_auth']:
        # cert puts cert and key file together
        # (cert_file_path, key_file_path)
        # Cert_file_path and key_file_ath are fully defined paths to
        # files on the appserver.
        logger.debug('Cert:%s , Key:%s' % (auth_state['cert_file'],
                                           auth_state['key_file']))

        cert = (auth_state['cert_file'], auth_state['key_file'])
    else:
        cert = ()

    header_info = generate_info_headers(request)

    # TODO: send header info to performance log
    logger.info(header_info)

    try:
        if timeout:
            r = requests.get(call_url,
                             cert=cert,
                             timeout=timeout,
                             headers=header_info,
                             verify=verify_state)
        else:
            r = requests.get(call_url,
                             cert=cert,
                             headers=header_info,
                             verify=verify_state)

        logger.debug("Request.get:%s" % call_url)
        logger.debug("Status of Request:%s" % r.status_code)

        fhir_response = build_fhir_response(request, call_url, cx, r=r, e=None)

        logger.debug("Leaving request_call with "
                     "fhir_Response: %s" % fhir_response)

        return fhir_response

    except requests.exceptions.Timeout as e:

        logger.debug("Gateway timeout talking to back-end server")
        fhir_response = build_fhir_response(request, call_url, cx, r=None, e=e)

        return fhir_response

    except requests.ConnectionError as e:
        logger.debug("Request.GET:%s" % request.GET)

        fhir_response = build_fhir_response(request, call_url, cx, r=None, e=e)

        return fhir_response

    except requests.exceptions.HTTPError as e:
        r_err = requests.exceptions.RequestException
        logger.debug('Problem connecting to FHIR Server: %s' % call_url)
        logger.debug('Exception: %s' % r_err)
        handle_e = handle_http_error(e)
        handle_e = handle_e

        fhir_response = build_fhir_response(request, call_url, cx, r=None, e=e)

        messages.error(request, 'Problem connecting to FHIR Server.')

        e = requests.Response
        logger.debug("HTTPError Status_code:%s" %
                     requests.exceptions.HTTPError)
        return fhir_response

    return fhir_response


def request_get_with_parms(request,
                           call_url,
                           search_params={},
                           cx=None,
                           timeout=None):
    """  call to request or redirect on fail
    call_url = target server URL and search parameters to be sent
    cx = Crosswalk record. The crosswalk is keyed off Request.user
    timoeout allows a timeout in seconds to be set.

    FhirServer is joined to Crosswalk.
    FhirServerAuth and FhirServerVerify receive cx and lookup
       values in the linked fhir_server model.

    """

    # Updated to receive cx (Crosswalk entry for user)
    # call FhirServer_Auth(cx) to get authentication
    auth_state = FhirServerAuth(cx)

    logger.debug("Auth_state:%s" % auth_state)

    verify_state = FhirServerVerify(cx)
    if auth_state['client_auth']:
        # cert puts cert and key file together
        # (cert_file_path, key_file_path)
        # Cert_file_path and key_file_ath are fully defined paths to
        # files on the appserver.
        logger.debug('Cert:%s , Key:%s' % (auth_state['cert_file'],
                                           auth_state['key_file']))

        cert = (auth_state['cert_file'], auth_state['key_file'])
    else:
        cert = ()

    logger.debug("\nrequest.get settings:%s\n"
                 "params=%s\n"
                 "cert:%s\ntimeout:%s\n"
                 "verify:%s\n"
                 "======="
                 "========\n" % (call_url,
                                 search_params,
                                 cert,
                                 timeout,
                                 verify_state))

    for k, v in search_params.items():
        logger.debug("\nkey:%s - value:%s" % (k, v))

    try:
        if timeout:
            r = requests.get(call_url,
                             params=search_params,
                             cert=cert,
                             timeout=timeout,
                             verify=verify_state)
        else:
            r = requests.get(call_url,
                             params=search_params,
                             cert=cert,
                             verify=verify_state)

        logger.debug("Request.get:%s" % call_url)
        logger.debug("Status of Request:%s" % r.status_code)

        fhir_response = build_fhir_response(request, call_url, cx, r=r, e=None)

        logger.debug("Leaving request_call_with_parms with "
                     "fhir_Response: %s" % fhir_response)

        return fhir_response

    except requests.exceptions.Timeout as e:

        logger.debug("Gateway timeout talking to back-end server")
        fhir_response = build_fhir_response(request, call_url, cx, r=None, e=e)

        return fhir_response

    except requests.ConnectionError as e:
        logger.debug("Request.GET:%s" % request.GET)

        fhir_response = build_fhir_response(request, call_url, cx, r=None, e=e)

        return fhir_response

    except requests.exceptions.HTTPError as e:
        r_err = requests.exceptions.RequestException
        logger.debug('Problem connecting to FHIR Server: %s' % call_url)
        logger.debug('Exception: %s' % r_err)
        handle_e = handle_http_error(e)
        handle_e = handle_e

        fhir_response = build_fhir_response(request, call_url, cx, r=None, e=e)

        messages.error(request, 'Problem connecting to FHIR Server.')

        e = requests.Response
        logger.debug("HTTPError Status_code:%s" %
                     requests.exceptions.HTTPError)

    return fhir_response


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

# Mark for removal ...remove related settings from base.


def block_params(get, srtc):
    """ strip parameters from search string - get is a dict """

    # Get parameters
    # split on &
    # get srtc.search_block as list
    if get:
        # set search_params to what is received as a default
        search_params = get
    else:
        return ''

    # Now we need to see if there are any get parameters to remove
    if srtc and srtc.override_search:
        search_params = get_url_query_string(get, srtc.get_search_block())

    return search_params


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
    # logger.debug('Evaluating: %s to remove:%s' % (get, skip_parm))

    filtered_dict = OrderedDict()

    # Check we got a get dict
    if not get:
        return filtered_dict
    if not isinstance(get, dict):
        return filtered_dict

    # Now we work through the parameters

    for k, v in get.items():

        logger_debug.debug('K/V: [%s/%s]' % (k, v))

        if k in skip_parm:
            pass
        else:
            # Build the query_string
            filtered_dict[k] = v

    # qs = urlencode(filtered_dict)
    qs = filtered_dict

    # logger.debug('Filtered parameters:%s from:%s' % (qs, filtered_dict))
    return qs


def FhirServerAuth(cx=None):
    # Get default clientauth settings from base.py
    # Receive a crosswalk.id or None
    # Return a dict

    auth_settings = {}
    if cx is None:
        rr = get_resourcerouter()
        auth_settings['client_auth'] = rr.client_auth
        auth_settings['cert_file'] = rr.cert_file
        auth_settings['key_file'] = rr.key_file
    else:
        # cx is passed in
        auth_settings['client_auth'] = cx.fhir_source.client_auth
        auth_settings['cert_file'] = cx.fhir_source.cert_file
        auth_settings['key_file'] = cx.fhir_source.key_file

    if auth_settings['client_auth']:
        # join settings.FHIR_CLIENT_CERTSTORE to cert_file and key_file
        cert_file_path = os.path.join(settings.FHIR_CLIENT_CERTSTORE,
                                      auth_settings['cert_file'])
        key_file_path = os.path.join(settings.FHIR_CLIENT_CERTSTORE,
                                     auth_settings['key_file'])
        auth_settings['cert_file'] = cert_file_path
        auth_settings['key_file'] = key_file_path

    return auth_settings


def FhirServerVerify(cx=None):
    # Get default Server Verify Setting
    # Return True or False (Default)

    verify_setting = False
    if cx:
        verify_setting = cx.fhir_source.server_verify

    return verify_setting


def FhirServerUrl(server=None, path=None, release=None):

    rr_def = get_resourcerouter()

    rr_server_address = rr_def.server_address

    fhir_server = notNone(server, rr_server_address)

    fhir_path = notNone(path, rr_def.server_path)

    fhir_release = notNone(release, rr_def.server_release)

    if fhir_release is not None:
        if not fhir_release.endswith('/'):
            fhir_release += '/'

    result = fhir_server
    if result is not None:
        result += fhir_path
    if result is not None:
        result += fhir_release
    # Set to "" if still None
    if result is None:
        result = ""

    return result


def check_access_interaction_and_resource_type(resource_type, intn_type, rr):
    """ usage is deny = check_access_interaction_and_resource_type()
    :param
    resource_type: resource
    intn_type: interaction type
    rr: ResourceRouter
    """

    try:
        rt = SupportedResourceType.objects.get(resourceType=resource_type,
                                               fhir_source=rr)
        # force comparison to lower case to make case insensitive check
        if str(intn_type).lower() not in rt.get_supported_interaction_types():
            msg = 'The interaction: %s is not permitted on %s FHIR ' \
                  'resources on this FHIR sever.' % (intn_type,
                                                     resource_type)
            logger_debug.debug(msg="%s:%s" % ("403", msg))
            return kickout_403(msg)
    except SupportedResourceType.DoesNotExist:
        msg = '%s is not a supported resource ' \
              'type on this FHIR server.' % resource_type
        logger_debug.debug(msg="%s:%s" % ("404", msg))
        return kickout_404(msg)

    return False


def check_rt_controls(resource_type, rr=None):
    # Check for controls to apply to this resource_type
    # logger.debug('Resource_Type =%s' % resource_type)
    # We may get more than one resourceType returned.
    # We need to deal with that.
    # Best option is to pass fhir_server from Crosswalk to this call

    if rr is None:
        rr = get_resourcerouter()

    try:
        srtc = SupportedResourceType.objects.get(resourceType=resource_type,
                                                 fhir_source=rr)
    except SupportedResourceType.DoesNotExist:
        srtc = None

    return srtc


def masked(srtc=None):
    """ check if force_url_override is set in SupportedResourceType """
    mask = False
    if srtc:
        if srtc.override_url_id:
            mask = True

    return mask


def masked_id(res_type,
              crosswalk=None,
              srtc=None,
              orig_id=None,
              slash=True):
    """ Get the correct id
     if crosswalk.fhir_source.shard_by == resource_type

     """
    id = str(orig_id)
    if srtc:
        if srtc.override_url_id:
            if crosswalk:
                if res_type.lower() == crosswalk.fhir_source.shard_by.lower():
                    # logger.debug('Replacing %s
                    # with %s' % (id, crosswalk.fhir_id))
                    id = crosswalk.fhir_id

    if slash:
        id += '/'

    return id


def mask_with_this_url(request, host_path='', in_text='', find_url=''):
    """ find_url in in_text and replace with url for this server """

    if in_text == '':
        # No text to evaluate
        return in_text

    if find_url == '':
        # no string to find
        return in_text

    # Now we have something to do
    # Get the host name
    # replace_text = request.get_host()
    if host_path.endswith('/'):
        host_path = host_path[:-1]
    if type(in_text) is str:
        out_text = in_text.replace(find_url, host_path)

        logger_debug.debug('Replacing: [%s] with [%s]' % (find_url, host_path))
    else:
        out_text = in_text

        logger_debug.debug('Passing [%s] to [%s]' % (in_text, "out_text"))

    return out_text


def mask_list_with_host(request, host_path, in_text, urls_be_gone=[]):
    """ Replace a series of URLs with the host_name """

    if in_text == '':
        return in_text

    if len(urls_be_gone) == 0:
        # Nothing in the list to be replaced
        return in_text

    rr_def = get_resourcerouter()
    rr_def_server_address = rr_def.server_address

    if isinstance(rr_def_server_address, str):
        if rr_def_server_address not in urls_be_gone:

            urls_be_gone.append(rr_def_server_address)

    for kill_url in urls_be_gone:
        # work through the list making replacements
        if kill_url.endswith('/'):
            kill_url = kill_url[:-1]

        in_text = mask_with_this_url(request, host_path, in_text, kill_url)

    return in_text


def get_fhir_id(cx=None):
    """
    Get the fhir_id from crosswalk
    :param cx:
    :return: fhir_id or None
    """

    if cx is None:
        return None
    else:
        return cx.fhir_id


def get_host_url(request, resource_type=''):
    """ get the full url and split on resource_type """

    if request.is_secure():
        http_mode = 'https://'
    else:
        http_mode = 'http://'

    full_url = http_mode + request.get_host() + request.get_full_path()
    if resource_type == '':
        return full_url
    else:
        full_url_list = full_url.split(resource_type)

    # logger_debug.debug('Full_url as list:%s' % full_url_list)

    return full_url_list[0]


def get_fhir_source_name(cx=None):
    """
    Get cx.source.name from Crosswalk or return empty string
    :param cx:
    :return:
    """
    if cx is None:
        return ""
    else:
        return cx.fhir_source.name


def build_conformance_url():
    """ Build the Conformance URL call string """

    rr_def = get_resourcerouter()
    rr_def_server_address = rr_def.server_address

    call_to = rr_def_server_address
    call_to += rr_def.server_path
    call_to += rr_def.server_release
    call_to += '/metadata'

    return call_to


def post_process_request(request, host_path, r_text, rewrite_url_list):
    if r_text == "":
        return r_text

    pre_text = mask_list_with_host(request,
                                   host_path,
                                   r_text,
                                   rewrite_url_list)

    return json.loads(pre_text, object_pairs_hook=OrderedDict)


def prepend_q(pass_params):
    """ Add ? to parameters if needed """
    if len(pass_params) > 0:
        if pass_params.startswith('?'):
            pass
        else:
            pass_params = '?' + pass_params
    return pass_params


def get_default_path(resource_name, cx=None):
    """ Get default Path for resource """

    if cx:
        default_path = cx.fhir_source.fhir_url
    else:
        try:
            rr = get_resourcerouter()
            default_path = rr.fhir_url

        except ResourceRouter.DoesNotExist:
            # use the default FHIR Server URL
            default_path = FhirServerUrl()
            logger_debug.debug("\nNO MATCH for %s. "
                               "Setting to:%s" % (resource_name,
                                                  default_path))

    return default_path


def dt_patient_reference(user):
    """ Get Patient Reference from Crosswalk for user """

    if user:
        patient = crosswalk_patient_id(user)
        if patient:
            return {'reference': patient}

    return None


def crosswalk_patient_id(user):
    """ Get patient/id from Crosswalk for user """

    logger_debug.debug("\ncrosswalk_patient_id User:%s" % user)
    try:
        patient = Crosswalk.objects.get(user=user)
        if patient.fhir_id:
            return patient.fhir_id

    except Crosswalk.DoesNotExist:
        pass

    return None


def get_crosswalk(user):
    """ Receive Request.user and use as lookup in Crosswalk
        Return Crosswalk or None
    """

    if user is None or user.is_anonymous():
        return None

    try:
        patient = Crosswalk.objects.get(user=user)
        return patient
    except Crosswalk.DoesNotExist:
        pass

    return None


def get_resource_names(rr=None):
    """ Get names for all approved resources
        We need to receive FHIRServer and filter list
        :return list of FHIR resourceTypes
    """
    # TODO: filter by FHIRServer

    if rr is None:
        rr = get_resourcerouter()
    all_resources = SupportedResourceType.objects.filter(fhir_source=rr)
    resource_types = []
    for name in all_resources:
        # check resourceType not already loaded to list
        if name.resourceType in resource_types:
            pass
        else:
            # Get the resourceType into a list
            resource_types.append(name.resourceType)

    return resource_types


def get_resourcerouter(cx=None):
    """
    get the default from settings.FHIR_SERVER_DEFAULT

    :cx = Receive the crosswalk record
    :return ResourceRouter

    """

    if cx is None:
        # use the default setting
        rr = ResourceRouter.objects.get(pk=settings.FHIR_SERVER_DEFAULT)
    else:
        # use the user's default ResourceRouter from cx
        rr = cx.fhir_source

    return rr


def build_rewrite_list(cx=None):
    """
    Build the rewrite_list of server addresses

    :return: rewrite_list
    """

    rewrite_list = []
    if cx:
        rewrite_list.append(cx.fhir_source.fhir_url)

    rr = get_resourcerouter()
    # get the default ResourceRouter entry
    if rr.fhir_url not in rewrite_list:
        rewrite_list.append(rr.fhir_url)

    if isinstance(settings.FHIR_SERVER_CONF['REWRITE_FROM'], list):
        rewrite_list.extend(settings.FHIR_SERVER_CONF['REWRITE_FROM'])
    elif isinstance(settings.FHIR_SERVER_CONF['REWRITE_FROM'], str):
        rewrite_list.append(settings.FHIR_SERVER_CONF['REWRITE_FROM'])

    return rewrite_list


def handle_http_error(e):
    """ Handle http error from request_call

     This function is under development

     """
    logger.debug("In handle http_error - e:%s" % e)

    return e


def build_fhir_response(request, call_url, cx, r=None, e=None):
    """
    setup a response object to return up the chain with consistent content
    if requests hits an error fields like text or json don't get created.
    So the purpose of fhir_response is to create a predictable object that
    can be handled further up the stack.

    :return:
    """

    if r is None:
        r_dir = []
    else:
        r_dir = dir(r)

    if e is None:
        e_dir = []
    else:
        e_dir = dir(e)

    fhir_response = Fhir_Response(r)

    fhir_response.call_url = call_url
    fhir_response.cx = cx

    if len(r_dir) > 0:
        if 'status_code' in r_dir:
            fhir_response._status_code = r.status_code
        else:
            fhir_response._status_code = '000'

        if 'text' in r_dir:
            fhir_response._text = r.text
        else:
            fhir_response._text = "No Text returned"

        if 'json' in r_dir:
            fhir_response._json = r.json
        else:
            fhir_response._json = {}

        if 'user' in request:
            fhir_response._owner = request.user + ":"
        else:
            fhir_response._owner = ":"

        if 'resource_owner' in request:
            fhir_response._owner = request.resource_owner
        else:
            fhir_response._owner += ""

    elif len(e_dir) > 0:
        fhir_response.status_code = 504
        fhir_response._status_code = fhir_response.status_code
        fhir_response._json = {"errors": ["The gateway has timed out",
                                          "Failed to reach FHIR Database."],
                               "code": fhir_response.status_code,
                               "status_code": fhir_response.status_code,
                               "text": "The gateway has timed out"}
        fhir_response._text = fhir_response._json
        fhir_response._content = fhir_response._json
    else:
        fhir_response.status_code = '000'
        fhir_response._status_code = '000'
        fhir_response._text = "No Text returned"
        fhir_response._json = {}

        if 'user' in request:
            fhir_response._owner = request.user + ":"
        else:
            fhir_response._owner = ":"
        if 'resource_owner' in request:
            fhir_response._owner += request.resource_owner
        else:
            fhir_response._owner += ""

    if e:
        logger.debug("\ne_response:START\n")
        e_dir = dir(e)
        for k in e_dir:
            if k == "characters_written":
                pass
            elif k == 'arg':
                for i in e.arg:
                    logger.debug("arg:%s" % i)
            else:
                logger.debug("%s:%s" % (k, e.__getattribute__(k)))

        logger.debug("\ne_response:END\n")

    return fhir_response


def get_response_text(fhir_response=None):
    """
    fhir_response: Fhir_Response class returned from request call
    Receive the fhir_response and get the text element
    text is in response.text or response._text

    :param fhir_response:
    :return:
    """

    text_in = ""

    if not fhir_response:
        return ""

    try:
        text_in = fhir_response.text
        if len(text_in) > 0:
            return text_in
    except Exception:
        pass

    try:
        text_in = fhir_response._response.text
        if len(text_in) > 0:
            return text_in
    except Exception:
        pass

    try:
        text_in = fhir_response._text
        if len(text_in) > 0:
            return text_in

    except Exception:
        logger.debug("Nothing in ._text")
        logger.debug("giving up...")
        text_in = ""
        return text_in


def get_delegator(request, via_oauth=False):
    """
    When accessing by OAuth we need to replace the request.user with
    the request.resource_owner.
    This is the user giving the OAuth app permission to access
    resources on their behalf

    :return: delegator
    """

    if via_oauth:
        if 'resource_owner' in request:
            delegator = request.resource_owner
        else:
            delegator = request.user
    else:
        delegator = request.user

    return delegator


def build_oauth_resource(request, format_type="json"):
    """
    Create a resource entry for oauth endpoint(s) for insertion
    into the conformance/capabilityStatement

    :return: security
    """
    endpoints = build_endpoint_info(OrderedDict(),
                                    issuer=base_issuer(request))
    logger.info("\nEndpoints:%s" % endpoints)

    if format_type.lower() == "xml":

        security = """
<security>
    <extension url="http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris">
        <extension url="token">
            <valueUri>%s</valueUri>
        </extension>
        <extension url="authorize">
            <valueUri>%s</valueUri>
        </extension>
    </extension>

</security>
        """ % (endpoints['token_endpoint'], endpoints['authorization_endpoint'])

    else:   # json

        security = {}

        security['extension'] = [
            {"url": "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris",
             "extension": [
                    {"url": "token",
                     "valueUri": endpoints['token_endpoint']},
                    {"url": "authorize",
                     "valueUri": endpoints['authorization_endpoint']}]
             }
        ]

    return security
