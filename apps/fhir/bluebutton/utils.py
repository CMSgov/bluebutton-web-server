import os
import json
import logging
import pytz
import requests
import uuid

from urllib.parse import urlencode
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

PRETTY_JSON_INDENT = 4

FORMAT_OPTIONS_CHOICES = ['json', 'xml']

DF_EXTRA_INFO = False

logger = logging.getLogger('hhs_server.%s' % __name__)
logger_error = logging.getLogger('hhs_server_error.%s' % __name__)
logger_debug = logging.getLogger('hhs_server_debug.%s' % __name__)
logger_info = logging.getLogger('hhs_server_info.%s' % __name__)

# consider removing fail_redirect and set a timeout for all calls that can
# be managed by settings.


def is_oauth2(request):
    """Is the request OAuth2 or not.  Return True or False."""
    if hasattr(request, 'resource_owner'):
        return True
    return False


def get_user_from_request(request):
    """Returns a user or None with login or OAuth2 API"""
    user = None
    if hasattr(request, 'resource_owner'):
        user = request.resource_owner
    if hasattr(request, 'user'):
        if not request.user.is_anonymous():
            user = request.user
    return user


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

    return result


def request_call(request, call_url, cx=None, fail_redirect="/", timeout=None):
    """  call to request or redirect on fail
    call_url = target server URL and search parameters to be sent
    cx = Crosswalk record. The crosswalk is keyed off Request.user
    fail_redirect allows routing to a page on failure
    timoeout allows a timeout in seconds to be set.

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

        ####################################################################
        ####################################################################
        ####################################################################

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

        ####################################################################
        ####################################################################
        ####################################################################

        logger.debug("Request.get:%s" % call_url)

        logger.debug("Status of Request:%s" % r.status_code)

        fhir_response = build_fhir_response(request, call_url, cx, r=r, e=None)

        logger.debug("Leaving request_call with "
                     "fhir_Response: %s" % fhir_response)

        return fhir_response

        # if r.status_code in ERROR_CODE_LIST:
        #     r.raise_for_status()
        # # except requests.exceptions.HTTPError as r_err:

    except requests.exceptions.Timeout as e:

        logger.debug("Gateway timeout talking to back-end server")
        fhir_response = build_fhir_response(request,
                                            call_url,
                                            cx,
                                            r=None,
                                            e=e)

        return fhir_response

    except requests.ConnectionError as e:
        logger.debug("Request.GET:%s" % request.GET)

        fhir_response = build_fhir_response(request,
                                            call_url,
                                            cx,
                                            r=None,
                                            e=e)

        return fhir_response

    except requests.exceptions.HTTPError as e:
        # except requests.exceptions.RequestException as r_err:
        r_err = requests.exceptions.RequestException
        logger.debug('Problem connecting to FHIR Server: %s' % call_url)
        logger.debug('Exception: %s' % r_err)
        handle_e = handle_http_error(e)
        handle_e = handle_e

        fhir_response = build_fhir_response(request,
                                            call_url,
                                            cx,
                                            r=None,
                                            e=e)

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
                           fail_redirect="/",
                           timeout=None):
    """  call to request or redirect on fail
    call_url = target server URL and search parameters to be sent
    cx = Crosswalk record. The crosswalk is keyed off Request.user
    fail_redirect allows routing to a page on failure
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

        ####################################################################
        ####################################################################
        ####################################################################

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

        ####################################################################
        ####################################################################
        ####################################################################

        logger.debug("Request.get:%s" % call_url)
        logger.debug("Status of Request:%s" % r.status_code)

        fhir_response = build_fhir_response(request, call_url, cx, r=r, e=None)

        logger.debug("Leaving request_call_with_parms with "
                     "fhir_Response: %s" % fhir_response)

        return fhir_response

    except requests.exceptions.Timeout as e:

        logger.debug("Gateway timeout talking to back-end server")
        fhir_response = build_fhir_response(request,
                                            call_url,
                                            cx,
                                            r=None,
                                            e=e)

        return fhir_response

    except requests.ConnectionError as e:
        # logger.debug('Connection Problem to FHIR '
        #              'Server: %s : %s' % (call_url, e))
        logger.debug("Request.GET:%s" % request.GET)
        # logger.debug("what is in e:\n#######\n%s\n##########\n" % dir(e))

        fhir_response = build_fhir_response(request,
                                            call_url,
                                            cx,
                                            r=None,
                                            e=e)

        # for attr in dir(e):
        #     if attr == "characters_written":
        #         pass
        #     else:
        #         logger.debug("e.%s = %s" % (attr, getattr(e, attr)))
        # e.status_code = 504
        # e.text = '{\"errors\": [\"Connection Problem to FHIR Server\", \"status_code: 504\"], \"code\": 504}'
        # logger.debug("what is in amended e:\n#######\n%s\n##########\n" % dir(e))
        #
        # return error_status(e, 504, reason=e.text)

        return fhir_response

    except requests.exceptions.HTTPError as e:
        # except requests.exceptions.RequestException as r_err:
        r_err = requests.exceptions.RequestException
        logger.debug('Problem connecting to FHIR Server: %s' % call_url)
        logger.debug('Exception: %s' % r_err)
        handle_e = handle_http_error(e)
        handle_e = handle_e

        fhir_response = build_fhir_response(request,
                                            call_url,
                                            cx,
                                            r=None,
                                            e=e)

        messages.error(request, 'Problem connecting to FHIR Server.')

        e = requests.Response
        # e.text = r_err
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
        # No get parameters to process so return
        search_params = ''
        return search_params

    # Now we need to see if there are any get parameters to remove
    if srtc:
        if srtc.override_search:
            search_params = get_url_query_string(get, srtc.get_search_block())

    # do we need to convert result to json. source could be
    # OrderedDict or string
    # search_params_result = json.dumps(search_params)

    # return search_params_result
    return search_params


def add_params(srtc, patient_id=None, key=None):
    """ Add filtering parameters to search string """

    # srtc.get_search_add will return a list
    # this will be in form 'Patient={Value}'
    # Replaceable parameters can be included
    # Currently Supported Replaceable Parameters are:
    # %PATIENT% = key
    # key = FHIR_ID for search parameter. eg. patient= Patient profile Id
    # modify this function to add more Replaceable Parameters
    # Need to suppress addition of patient={id} in Patient resource read

    # Returns List

    # add_params = ''
    add_params = []

    if srtc:
        if srtc.override_search:
            params_list = srtc.get_search_add()
            if isinstance(params_list, list):
                pass
            else:
                if params_list == "[]":
                    params_list = []
                else:
                    params_list = [params_list, ]

            logger_debug.debug('Parameters to add:%s' % params_list)
            logger_debug.debug('key to replace: %s' % key)

            add_params = []
            for item in params_list:
                # Run through list and do variable replacement
                if srtc.resourceType.lower() not in item.lower():
                    # only replace 'patient=%PATIENT%' if resource not Patient
                    if '%PATIENT%' in item:
                        if key is None:
                            patient_str = str(patient_id)
                            if patient_id is None:
                                patient_str = ''
                        else:
                            # force key to string
                            patient_str = str(key)
                        if patient_str is 'None':
                            patient_str = ''
                        if patient_str is None:
                            patient_str = ''
                        item = item.replace('%PATIENT%', patient_str)
                        if '%PATIENT%' in item:
                            # Still there we need to remove
                            item = item.replace('%PATIENT%', '')

                    add_params.append(item)
            logger_debug.debug(
                'Resulting additional parameters:%s' % add_params)

    return add_params


def concat_parms(front_part={}, back_part={}):
    """ Concatenate the Query Parameters Strings
        The strings should be urlencoded.

    """

    joined_parms = OrderedDict()

    logger_debug.debug('Joining %s with: %s' % (front_part, back_part))
    if len(front_part) > 0:
        if isinstance(front_part, dict):
            for k, v in front_part.items():
                # append back items
                joined_parms[k] = v
        elif isinstance(front_part, list):
            for item in front_part:
                # split item  on '=' eg. patient=4995802
                item_split = item.split('=')
                if len(item_split) > 1:
                    joined_parms[item_split[0]] = item_split[1]
                else:
                    joined_parms[item_split[0]] = ''

    if len(back_part) > 0:
        if isinstance(back_part, dict):
            for k, v in back_part.items():
                # append back items
                joined_parms[k] = v
        elif isinstance(back_part, list):
            for item in back_part:
                # split item  on '=' eg. patient=4995802
                item_split = item.split('=')
                if len(item_split) > 1:
                    joined_parms[item_split[0]] = item_split[1]
                else:
                    joined_parms[item_split[0]] = ''

    concat_parm = '?' + urlencode(joined_parms)
    logger_debug.debug("Concat_parm:%s" % concat_parm)
    if concat_parm.startswith('?='):
        concat_parms = '?' + concat_parm[3:]
    else:
        concat_parms = concat_parm
    logger_debug.debug('resulting string:%s' % concat_parms)
    return concat_parms


def build_params(get, srtc, key, patient_id=None):
    """
    Build the URL Parameters.
    We have to skip any in the skip list.

    :param get:
    :param srtc:
    :param key:
    :return: all_param
    """

    # First we strip the parameters that need to be blocked
    url_param = block_params(get, srtc)

    # Now we need to construct the parameters we need to add

    add_param = add_params(srtc, patient_id=patient_id, key=key)

    # Put the parameters together in urlencoded string
    # leading ? and parameters joined by &
    all_param = concat_parms(url_param, add_param)

    logger.debug('Parameter (post block/add):%s' % all_param)

    # now we check for _format being specified. Otherwise we get back html
    # by default we will process json unless _format is already set.

    all_param = add_format(all_param)

    logger.debug('add_Format returned:%s' % all_param)

    return all_param


def add_format(all_param=''):
    """
    Check for _format in parameters and add if missing
    """

    # logger.debug("Checking _FORMAT:%s" % all_param)
    if '_format' in all_param:
        # We have a _format setting.
        # Let's check for xml or json.
        if '_format=json' in all_param.lower():
            return all_param
        elif '_format=xml' in all_param.lower():
            return all_param

    # no _format set.
    # Let's set _format=json.
    if all_param != '':
        all_param += '&'
    else:
        all_param = '?'

    all_param += '_format=json'

    return all_param


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
        # No text to evaluate
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

        # logger_debug.debug("Replacing:%s" % kill_url)

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


def build_output_dict(request,
                      od,
                      resource_type,
                      key,
                      vid,
                      interaction_type,
                      fmt,
                      text_out):
    """ Create the output as an OrderedDict """

    od['resource_type'] = resource_type
    od['id'] = key
    if vid is not None:
        od['vid'] = vid

    # logger_debug.debug('Query List:%s' % request.META['QUERY_STRING'])

    if DF_EXTRA_INFO:
        od['request_method'] = request.method
        od['interaction_type'] = interaction_type
        od['parameters'] = request.GET.urlencode()

        logger_debug.debug('or:%s' % od['parameters'])

        od['format'] = fmt
        od['note'] = 'This is the %s Pass Thru ' \
                     '(%s) ' % (resource_type, key)

    od['bundle'] = text_out

    return od


def post_process_request(request,
                         ct_fmt,
                         host_path,
                         r_text,
                         rewrite_url_list):
    """ Process request based on xml or json fmt """

    if r_text == "":
        # Return nothing
        return r_text

    if ct_fmt.lower() == 'xml' or ct_fmt.lower() == 'html':
        # We will add xml support later

        text_out = mask_list_with_host(request,
                                       host_path,
                                       r_text,
                                       rewrite_url_list)
        # text_out= minidom.parseString(text_out).toprettyxml()
    else:
        # dealing with json
        # text_out = r.json()
        pre_text = mask_list_with_host(request,
                                       host_path,
                                       r_text,
                                       rewrite_url_list)
        # logger_debug.debug("\n\nPRE_TEXT:%s\n\n" % pre_text)
        text_out = json.loads(pre_text, object_pairs_hook=OrderedDict)

    return text_out


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

    # logger_debug.debug("\nGET_DEFAULT_URL:%s" % resource_name)
    if cx:
        default_path = cx.fhir_source.fhir_url
    else:
        try:
            rr = get_resourcerouter()
            default_path = rr.fhir_url
            # logger_debug.debug("\nDEFAULT_URL=%s" % default_path)

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
    # Don't do a lookup if user is not defined
    if user is None:
        return None

    if user.is_anonymous():
        return None

    # Don't do a lookup on a user who is not logged in
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

    # logger.debug("r to work with:\n%s\n#####################\n" % r_dir)

    if e is None:
        e_dir = []
    else:
        e_dir = dir(e)
    # logger.debug("e to deal with:\n%s\n#####################\n" % e_dir)

    # if 'status_code' in r_dir:
    #     logger.debug("r status:%s\n" % r.status_code)
    # else:
    #     logger.debug("r status: not returned\n")

    fhir_response = Fhir_Response(r)

    fhir_response.call_url = call_url
    fhir_response.cx = cx

    if len(r_dir) > 0:

        # logger.debug("r._content:%s" % r._content)

        if 'status_code' in r_dir:
            fhir_response._status_code = r.status_code
        else:
            fhir_response._status_code = '000'

        if 'text' in r_dir:
            fhir_response._text = r.text

            if r.text[0] == "<":
                logger.debug("\nLooks like XML....[%s]" % r.text[:10])
                fhir_response._xml = r.text

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
        # logger.debug("e._content:%s" % e._content)
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

    # logger.debug("\nfhir_response:%s" % dir(fhir_response))
    # logger.debug("\nChecking .text:%s\n"
    #              "_response.text:%s\n"
    #              "and _text:%s\n" % (fhir_response.text[:40],
    #                                  fhir_response._response.text[:40],
    #                                  fhir_response._text[:40]))

    text_in = ""

    if not fhir_response:
        text_in = ""
        return text_in

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
            # logger.debug("returning "
            #              "_text:%s" % fhir_response._text[:40])
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
