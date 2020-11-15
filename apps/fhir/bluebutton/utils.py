import os
import logging
import pytz
import requests
import uuid

from collections import OrderedDict
from datetime import datetime
from pytz import timezone

from django.conf import settings
from django.contrib import messages
from apps.fhir.server.settings import fhir_settings

from oauth2_provider.models import AccessToken

from apps.wellknown.views import (base_issuer, build_endpoint_info)
from .models import Crosswalk, Fhir_Response

logger = logging.getLogger('hhs_server.%s' % __name__)
logger_perf = logging.getLogger('performance')


def get_user_from_request(request):
    """Returns a user or None with login or OAuth2 API"""
    user = None
    if hasattr(request, 'resource_owner'):
        user = request.resource_owner
    if hasattr(request, 'user'):
        if not request.user.is_anonymous:
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
    if 'HTTP_AUTHORIZATION' in request.META:
        auth_list = request.META['HTTP_AUTHORIZATION'].split(' ')
    elif 'Authorization' in request.META:
        auth_list = request.META['Authorization'].split(' ')
    else:
        auth_list = []

    # Get bearer token from str split list
    if len(auth_list) == 2:
        token = auth_list[1]

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
    # BB2-279 support BFD header "includeAddressFields" and always set to False
    # NOT TO include addresss info in Patient resource (refer BFD-379)
    result['includeAddressFields'] = 'False'
    # get timestamp from request via Middleware, or get current time
    result['BlueButton-OriginalQueryTimestamp'] = str(get_timestamp(request))

    # get uuid or set one
    result['BlueButton-OriginalQueryId'] = str(get_query_id(request))

    # get query counter or set to 1
    result['BlueButton-OriginalQueryCounter'] = str(get_query_counter(request))

    # Return resource_owner or user
    user = get_user_from_request(request)
    crosswalk = get_crosswalk(user)
    if crosswalk:
        # we need to send the HicnHash or the fhir_id
        if crosswalk.fhir_id is not None:
            result['BlueButton-BeneficiaryId'] = 'patientId:' + str(crosswalk.fhir_id)
        else:
            result['BlueButton-BeneficiaryId'] = 'hicnHash:' + str(crosswalk.user_hicn_hash)
    else:
        # Set to empty
        result['BlueButton-BeneficiaryId'] = ""

    if user:
        result['BlueButton-UserId'] = str(user.id)
        # result['BlueButton-User'] = str(user)
        result['BlueButton-Application'] = ""
        result['BlueButton-ApplicationId'] = ""
        if AccessToken.objects.filter(token=get_access_token_from_request(request)).exists():
            at = AccessToken.objects.get(token=get_access_token_from_request(request))
            result['BlueButton-Application'] = str(at.application.name)
            result['BlueButton-ApplicationId'] = str(at.application.id)
            result['BlueButton-DeveloperId'] = str(at.application.user.id)
            # result['BlueButton-Developer'] = str(at.application.user)
        else:
            result['BlueButton-Application'] = ""
            result['BlueButton-ApplicationId'] = ""
            result['BlueButton-DeveloperId'] = ""
            result['BlueButton-Developer'] = ""

    return result


def set_default_header(request, header=None):
    """
    Set default values in header for call to back-end
    :param request:
    :param header:
    :return: header
    """

    if header is None:
        header = {}

    header['keep-alive'] = settings.REQUEST_EOB_KEEP_ALIVE
    if request.is_secure():
        header['X-Forwarded-Proto'] = "https"
    else:
        header['X-Forwarded-Proto'] = "http"

    header['X-Forwarded-Host'] = request.get_host()

    originating_ip = get_ip_from_request(request)
    if originating_ip:
        header['X-Forwarded-For'] = originating_ip
    else:
        header['X-Forwarded-For'] = ""

    return header


def request_call(request, call_url, crosswalk=None, timeout=None, get_parameters={}):
    """  call to request or redirect on fail
    call_url = target server URL and search parameters to be sent
    crosswalk = Crosswalk record. The crosswalk is keyed off Request.user
    timeout allows a timeout in seconds to be set.

    FhirServer is joined to Crosswalk.
    FhirServerAuth and FhirServerVerify receive crosswalk and lookup
       values in the linked fhir_server model.

    """

    # Updated to receive crosswalk (Crosswalk entry for user)
    # call FhirServer_Auth(crosswalk) to get authentication
    auth_state = FhirServerAuth(crosswalk)

    verify_state = FhirServerVerify(crosswalk)
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

    header_info = set_default_header(request, header_info)

    header_detail = header_info
    header_detail['BlueButton-OriginalUrl'] = request.path
    header_detail['BlueButton-OriginalQuery'] = request.META['QUERY_STRING']
    header_detail['BlueButton-BackendCall'] = call_url

    logger_perf.info(header_detail)

    try:
        if timeout:
            r = requests.get(call_url,
                             cert=cert,
                             params=get_parameters,
                             timeout=timeout,
                             headers=header_info,
                             verify=verify_state)
        else:
            r = requests.get(call_url,
                             cert=cert,
                             params=get_parameters,
                             headers=header_info,
                             verify=verify_state)

        logger.debug("Request.get:%s" % call_url)
        logger.debug("Status of Request:%s" % r.status_code)

        header_detail['BlueButton-BackendResponse'] = r.status_code

        logger_perf.info(header_detail)

        fhir_response = build_fhir_response(request, call_url, crosswalk, r=r, e=None)

        logger.debug("Leaving request_call with "
                     "fhir_Response: %s" % fhir_response)

    except requests.exceptions.Timeout as e:

        logger.debug("Gateway timeout talking to back-end server")
        fhir_response = build_fhir_response(request, call_url, crosswalk, r=None, e=e)

    except requests.ConnectionError as e:
        logger.debug("Request.GET:%s" % request.GET)

        fhir_response = build_fhir_response(request, call_url, crosswalk, r=None, e=e)

    except requests.exceptions.HTTPError as e:
        r_err = requests.exceptions.RequestException
        logger.debug('Problem connecting to FHIR Server: %s' % call_url)
        logger.debug('Exception: %s' % r_err)
        handle_http_error(e)

        fhir_response = build_fhir_response(request, call_url, crosswalk, r=None, e=e)

        messages.error(request, 'Problem connecting to FHIR Server.')

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


def FhirServerAuth(crosswalk=None):
    # Get default clientauth settings from base.py
    # Receive a crosswalk.id or None
    # Return a dict

    auth_settings = {}
    resource_router = get_resourcerouter()
    auth_settings['client_auth'] = resource_router.client_auth
    auth_settings['cert_file'] = resource_router.cert_file
    auth_settings['key_file'] = resource_router.key_file

    if auth_settings['client_auth']:
        # join settings.FHIR_CLIENT_CERTSTORE to cert_file and key_file
        cert_file_path = os.path.join(settings.FHIR_CLIENT_CERTSTORE,
                                      auth_settings['cert_file'])
        key_file_path = os.path.join(settings.FHIR_CLIENT_CERTSTORE,
                                     auth_settings['key_file'])
        auth_settings['cert_file'] = cert_file_path
        auth_settings['key_file'] = key_file_path

    return auth_settings


def FhirServerVerify(crosswalk=None):
    # Get default Server Verify Setting
    # Return True or False (Default)
    return get_resourcerouter().verify_server


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

        logger.debug('Replacing: [%s] with [%s]' % (find_url, host_path))
    else:
        out_text = in_text

        logger.debug('Passing [%s] to [%s]' % (in_text, "out_text"))

    return out_text


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

    return full_url_list[0]


def prepend_q(pass_params):
    """ Add ? to parameters if needed """
    if len(pass_params) > 0:
        if pass_params.startswith('?'):
            pass
        else:
            pass_params = '?' + pass_params
    return pass_params


def dt_patient_reference(user):
    """ Get Patient Reference from Crosswalk for user """

    if user:
        patient = crosswalk_patient_id(user)
        if patient:
            return {'reference': patient}

    return None


def crosswalk_patient_id(user):
    """ Get patient/id from Crosswalk for user """

    logger.debug("\ncrosswalk_patient_id User:%s" % user)
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

    if user is None or user.is_anonymous:
        return None

    try:
        patient = Crosswalk.objects.get(user=user)
        return patient
    except Crosswalk.DoesNotExist:
        pass

    return None


def get_resourcerouter(crosswalk=None):
    return fhir_settings


def handle_http_error(e):
    """ Handle http error from request_call

     This function is under development

     """
    logger.debug("In handle http_error - e:%s" % e)

    return e


def build_fhir_response(request, call_url, crosswalk, r=None, e=None):
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
    fhir_response.crosswalk = crosswalk

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
    <cors>true</cors>
    <service>
        <text>OAuth</text>
        <coding>
            <system url="http://hl7.org/fhir/restful-security-service">
            <code>OAuth</code>
            <display>OAuth</display>
        </coding>
    </service>
    <service>
        <text>SMART-on-FHIR</text>
        <coding>
            <system url="http://hl7.org/fhir/restful-security-service">
            <code>SMART-on-FHIR</code>
            <display>SMART-on-FHIR</display>
        </coding>
    </service>
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

        security['cors'] = True
        security['service'] = [
            {
                "text": "OAuth",
                "coding": [{
                    "system": "http://hl7.org/fhir/restful-security-service",
                    "code": "OAuth",
                    "display": "OAuth"
                }]
            }, {
                "text": "OAuth2 using SMART-on-FHIR profile (see http://docs.smarthealthit.org)",
                "coding": [{
                    "system": "http://hl7.org/fhir/restful-security-service",
                    "code": "SMART-on-FHIR",
                    "display": "SMART-on-FHIR"
                }]
            }]
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


def get_patient_by_id(id, request):
    '''
    a helper adapted to just get patient given an id out of band of auth flow
    or noraml data flow, use by tools such as BB2-Tools admin viewers
    '''
    auth_settings = FhirServerAuth(None)
    certs = (auth_settings['cert_file'], auth_settings['key_file'])
    headers = generate_info_headers(request)
    headers['BlueButton-Application'] = "BB2-Tools"
    headers['includeIdentifiers'] = "true"
    url = "{}Patient/{}?_format={}".format(get_resourcerouter().fhir_url, id, settings.FHIR_PARAM_FORMAT)
    s = requests.Session()
    req = requests.Request('GET', url, headers=headers)
    prepped = req.prepare()
    response = s.send(prepped, cert=certs, verify=False)
    response.raise_for_status()
    return response.json()
