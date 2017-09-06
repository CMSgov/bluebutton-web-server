import json
import logging

# try:
#     # python2
#     from urllib import urlencode
# except ImportError:
#     # python3
#     from urllib.parse import urlencode

try:
    # python2
    from urlparse import parse_qs
except ImportError:
    # python3
    from urllib.parse import parse_qs

from collections import OrderedDict
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse

from apps.fhir.server.models import SupportedResourceType, ResourceRouter

logger = logging.getLogger('hhs_server.%s' % __name__)

# ERROR_CODE_LIST = [301, 302, 400, 401, 402, 403, 404, 500, 501, 502, 503, 504]
ERROR_CODE_LIST = [301, 302, 401, 402, 403, 404, 500, 501, 502, 503, 504]

SESSION_KEY = 'BBF_search_session'


def kickout_301(reason, status_code=301):
    """ 301 Moved Permanently """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason]
    return HttpResponse(json.dumps(response, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_302(reason, status_code=302):
    """ 302 Temporarily Moved """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason]
    return HttpResponse(json.dumps(response, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_400(reason, status_code=400):
    """ 400 Bad Request """
    oo = OrderedDict()
    oo['resourceType'] = 'OperationOutcome'
    oo['code'] = status_code
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity'] = 'fatal'
    issue['code'] = 'exception'
    issue['details'] = reason
    return HttpResponse(json.dumps(oo, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_401(reason, status_code=401):
    """ 401 Unauthorized """
    oo = OrderedDict()
    oo['resourceType'] = 'OperationOutcome'
    oo['code'] = status_code
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity'] = 'fatal'
    issue['code'] = 'security'
    issue['details'] = reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_402(reason, status_code=402):
    """ 402 Payment Required """
    oo = OrderedDict()
    oo['resourceType'] = 'OperationOutcome'
    oo['code'] = status_code
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity'] = 'fatal'
    issue['code'] = 'security'
    issue['details'] = reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_403(reason, status_code=403):
    """ 403 Forbidden """
    oo = OrderedDict()
    oo['resourceType'] = 'OperationOutcome'
    oo['code'] = status_code
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity'] = 'fatal'
    issue['code'] = 'security'
    issue['details'] = reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_404(reason, status_code=404):
    """ 404 Not Found """
    oo = OrderedDict()
    oo['resourceType'] = 'OperationOutcome'
    oo['code'] = status_code
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity'] = 'fatal'
    issue['code'] = 'not-found'
    issue['details'] = reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_500(reason, status_code=500):
    """ 500 Internal Server Error """
    oo = OrderedDict()
    oo['resourceType'] = 'OperationOutcome'
    oo['code'] = status_code
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity'] = 'fatal'
    issue['code'] = 'exception'
    issue['details'] = reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_501(reason, status_code=501):
    """ 501 Not Implemented """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason, 'Not Implemented']
    return HttpResponse(json.dumps(response, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_502(reason, status_code=502):
    """ 502 Bad Gateway """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason, 'Bad Gateway']
    return HttpResponse(json.dumps(response, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_503(reason, status_code=503):
    """ 503 Gateway Timeout """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason, 'Gateway Timeout']
    return HttpResponse(json.dumps(response, indent=4),
                        status=status_code,
                        content_type='application/json')


def kickout_504(reason, status_code=504):
    """ 504 Gateway Timeout """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason, 'Gateway Timeout']
    return HttpResponse(json.dumps(response, indent=4),
                        status=status_code,
                        content_type='application/json')


def error_status(r, status_code=404, reason='undefined error occurred'):
    """
    Generate an error page
    based on fhir.utils.kickout_xxx
    :param r:
    :param status_code:
    :param reason:
    :return:
    """

    logger.debug("R:%s" % r)
    logger.debug("status_code:%s" % status_code)
    try:
        error_detail = r.text

        if settings.DEBUG:
            if r.text[0] == '<':
                error_detail = 'xml:'
                error_detail += r.text
            elif 'json' in r:
                error_detail = r.json
    except:
        error_detail = ""

    logger.debug("Reason:%s" % reason)
    if reason == 'undefined error occurred':
        if status_code == 404:
            reason = 'page not found'
            kickout_404(reason)
        elif status_code == 403:
            reason = 'You are not authorised to access this page. ' \
                     'Do you need to login?'
            kickout_403(reason)
        elif status_code == 402:
            reason = 'There is a Payment problem'
            kickout_402(reason)
        elif status_code == 401:
            reason = 'Unauthenticated - There was a problem with login'
            kickout_400(reason)
        elif status_code == 400:
            reason = 'There was a problem with the data'
            kickout_400(reason)
        elif status_code == 301:
            reason = 'The requested page has been permanently moved'
        elif status_code == 302:
            reason = 'The requested page has been temporarily moved'
            kickout_302(reason)
        elif status_code == 501:
            reason = 'Not Implemented'
            kickout_501(reason)
        elif status_code == 502:
            reason = 'Bad gateway'
            kickout_502(reason)
        elif status_code == 503:
            reason = 'Gateway service unavailable'
            kickout_503(reason)
        elif status_code == 504:
            reason = 'The gateway has timed out'
            kickout_504(reason)

    response = OrderedDict()

    response['errors'] = [reason, error_detail]
    response['code'] = status_code
    response['status_code'] = status_code
    response['text'] = reason

    logger.debug("Errors: %s" % response)

    return HttpResponse(json.dumps(response, indent=4),
                        status=status_code,
                        content_type='application/json')


def write_session(request, ikey, content, skey=SESSION_KEY):
    """ Write Session Variables for use in checking follow on search calls

    content = {
        'cache_id': ikey,
        'fhir_to': host_path,
        'rwrt_list': rewrite_url_list,
        'res_type': resource_type,
        'intn_type': interaction_type,
        'key': key,
        'vid': vid,
        'resource_router': rr.id
    }

    """
    now = datetime.now()
    # get search expiry from the ResourceRouter record
    rr_id = content['resource_router']
    try:
        rr = ResourceRouter.objects.get(id=rr_id)
        mins = (rr.server_search_expiry / 60)
    except ResourceRouter.DoesNotExist:
        mins = 30
    then = now + timedelta(minutes=mins)
    expiry = str(then)

    if skey not in request.session:
        search_keys = {}
        request.session[skey] = search_keys
    else:
        search_keys = request.session[skey]

    # print("Search Keys:%s - %s[%s]" % (skey,
    #                                    ikey,
    #                                    search_keys))

    # Now we have the total search dict with an expires setting
    if ikey not in search_keys:
        # print("\nContent:%s\n" % content)
        content['cache_id'] = ikey
        content['expires'] = expiry

        # print("\nContent:%s\n" % content)

        search_keys[ikey] = content
        # print("\nSession Content-Search_keys:%s:%s" % (skey, search_keys))

    else:
        old_content = search_keys[ikey]
        # print("\nreturned search_keys       :%s:%s" % (skey, search_keys))
        if isinstance(content, dict):
            # update content with whatever is submitted
            for k, v in content.items():
                old_content[k] = v

        # don't update the expires setting
        # don't update the cache_id

        # print("\nupdated session_content:%s:%s" % (skey, old_content))
        search_keys[ikey] = old_content
        # print("\nupdated     search keys:%s:%s" % (skey, search_keys))
    # write session variables back
    request.session[skey] = search_keys

    # logger.debug("\nWritten session:%s - %s:%s" % (skey,
    #                                                ikey,
    #                                                request.session[skey]))

    return True


def read_session(request, ikey, skey=SESSION_KEY):
    """ Read Session Variables when checking follow on search call

    content = {
        'cache_id': ikey,
        'fhir_to': host_path,
        'rwrt_list': rewrite_url_list,
        'res_type': resource_type,
        'intn_type': interaction_type,
        'key': key,
        'vid': vid,
        'resource_router': rr
    }

    """

    result = {}
    # action = "GET"
    now = str(datetime.now())

    if skey in request.session:
        # print("\n\nReading Session:%s - %s:%s" % (skey,
        #                                           ikey,
        #                                           request.session[skey]))
        if ikey in request.session[skey]:
            # print("\n\nfound key:%s" % ikey)
            session_keys = request.session[skey]
            if 'expires' in session_keys[ikey]:
                # print("\nChecking for Expiry..")
                if session_keys[ikey]['expires'] < now:
                    request.session[skey].pop(ikey, None)

                    # action = "DEL"
                    # print("\n\n Removed %s:%s" % (ikey, request.session[skey]))
                else:
                    # action = "PULL"
                    result = session_keys[ikey]
            else:
                # print("\n\nGetting Session Data:%s" % session_keys[ikey])
                result = session_keys[ikey]
                # action = "UNEXPIRED"
        else:
            # print("\n%s not found" % ikey)
            pass
    else:
        # action = "SKIP"
        pass

    # print("\n\nSession Key[%s]%s:%s:%s" % (skey, action, ikey, result))
    return result


def find_ikey(text_block):
    """ Get the _getpages value """

    ikey_pre = text_block.split('_getpages=')

    if len(ikey_pre) == 1:
        # no split
        return ''

    ikey = ikey_pre[1].split('_getpagesoffset=')

    if len(ikey) == 1:
        # We didn't get a cache_id
        # couldn't crop the text
        return ''

    if ikey[0].endswith('&amp;'):
        result = ikey[0][:-5]
    elif ikey[0].endswith('&'):
        result = ikey[0][:-1]
    else:
        result = ikey[0]

    return result


def get_search_param_format(search_parm):
    """ Check for _format={valid fhir formats}
    input should be request.META['QUERY_STRING']
    eg. xml+fhir
     or json+fhir
     or xml
     or json
     or html/json
     or html/xml
    """

    parameter_search = parse_qs(search_parm)
    logger.debug("evaluating for _format:%s [%s]" % (search_parm,
                                                     parameter_search))

    # Now do a hierarchy of checks
    # now we need check for "_format" in parameter_search
    check_case = None
    if "_format" in parameter_search:
        checks = ['html', 'xml', 'json']
        for c in checks:
            check_case = check_lcase_list_item(parameter_search['_format'], c)
            # logger.debug("we found a _format [%s] "
            #              "while checking for %s" % (check_case, c))
            if check_case:
                return check_case

    if "format" in parameter_search:
        checks = ['html', 'xml', 'json']
        for c in checks:
            check_case = check_lcase_list_item(parameter_search['format'], c)
            # logger.debug("we found format [%s] "
            #              "while checking for %s" % (check_case, c))
            if check_case:
                return check_case

    return ''


def check_for_element(search_dict, check_key, check_list):
    """

    :param search_dict:
    :param check_key:
    :param check_list:
    :return: ret_val
    """

    if check_key in search_dict:
        # logger.debug("Checking %s in %s" % (check_key, search_dict))
        for c in check_list:
            check_case = check_lcase_list_item(search_dict[check_key], c)
            # logger.debug("we found format:[%s] "
            #              "while checking for %s on key:%s" % (c,
            #                                                   check_case,
            #                                                   check_key))
            if check_case:
                return True

    return False


def check_lcase_list_item(list_value, check_for):
    """ search_param is a dict with each value as a list
        go through list to check for value. comparing as lowercase
     """

    # logger.debug("checking %s in %s" % (check_for, list_value))
    if type(check_for) is list:
        checking = check_for[0]
    else:
        checking = check_for
    if type(list_value) is not list:
        listing = [list_value, ]
    else:
        listing = list_value
    for l in listing:
        if checking.lower() in l.lower():
            # logger.debug("Found %s in %s" % (checking, l))
            return check_for
        else:
            # logger.debug("no luck with %s v  %s" % (checking, l))
            pass

    return None


def strip_format_for_back_end(pass_params):
    """
    check for _format in URL Parameters
    We need to force json or xml
    if html is included in _format we need to strip it out

    """

    # pass_params should arrive as an OrderedDict.
    # no need to parse
    parameter_search = pass_params
    # parameter_search = parse_qs(pass_params)
    logger.debug("evaluating [%s] for _format" % parameter_search)

    updated_parameters = OrderedDict()
    for k in parameter_search:
        if k.lower() == "_format":
            pass
        elif k.lower() == "format":
            pass
        else:
            updated_parameters[k] = parameter_search[k]

    # We have removed format setting now we need to add the
    # correct version to call the back end
    if check_for_element(parameter_search, "_format", ["html/xml",
                                                       "xml",
                                                       "xml+fhir",
                                                       "xml fhir"]):
        updated_parameters["_format"] = "xml"

    elif check_for_element(parameter_search, "format", ["html/xml",
                                                        "xml",
                                                        "xml+fhir",
                                                        "xml fhir"]):
        updated_parameters["_format"] = "xml"
    elif check_for_element(parameter_search, "_format", ["html/json",
                                                         "json",
                                                         "json+fhir",
                                                         "json fhir"]):
        updated_parameters["_format"] = "json"
    elif check_for_element(parameter_search, "format", ["html/json"","
                                                        "json",
                                                        "json+fhir",
                                                        "json fhir"]):
        updated_parameters["_format"] = "json"
    else:
        # We found nothing so we should set to default format of json
        updated_parameters["_format"] = "json"

    # rebuild the parameters
    logger.debug("Updated parameters:%s" % updated_parameters)
    # pass_params = urlencode(updated_parameters)
    pass_params = updated_parameters
    logger.debug("Returning updated parameters:%s" % pass_params)

    return pass_params


def get_target_url(fhir_url, resource_type):
    """ Strip down the target fhir_url for saving to session variable """

    if resource_type in fhir_url:
        # save without resource_type and ending slash
        save_url = fhir_url.split(resource_type)[0][:-1]
    else:
        if fhir_url.endswith('/'):
            save_url = fhir_url[:-1]
        else:
            save_url = fhir_url

    return save_url


def check_access_interaction_and_resource_type(resource_type, interaction_type):
    # We need to filter by FHIRServer or deal with multiple items
    try:
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        if interaction_type not in rt.get_supported_interaction_types():
            msg = 'The interaction {} is not permitted on {} FHIR resources on this FHIR sever.'.format(
                interaction_type, resource_type
            )
            return kickout_403(msg)
    except SupportedResourceType.DoesNotExist:
        msg = '{} is not a supported resource type on this FHIR server.'.format(resource_type)
        return kickout_404(msg)
    return False


def get_content_type(response):
    """ Check response headers for Content-Type
        expected options:
        application/json+fhir;charset=UTF-8
        application/xml+fhir;charset=UTF-8

    """
    if response.status_code in ERROR_CODE_LIST:
        return error_status(response, response.status_code)
    else:
        result = OrderedDict()
        result['Content-Type'] = response.headers.get("Content-Type")
        return result


def content_is_json_or_xml(response):
    """ Evaluate response.headers for Content-Type

        :return "json | xml """

    ct = get_content_type(response)
    if 'errors' in ct:
        ct_format = 'json'
    else:
        ct_format = "xml"
        if "json" in ct['Content-Type'].lower():
            ct_format = "json"

    return ct_format


def valid_interaction(resource, rr):
    """ Create a list of Interactions for the resource
        We need to deal with multiple objects returned or filter by FHIRServer
    """

    interaction_list = []
    try:
        resource_interaction = \
            SupportedResourceType.objects.get(resourceType=resource,
                                              fhir_source=rr)
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


def request_format(query_params):
    """
    Save the _format or format received
    :param query_params:
    :return:
    """

    # Let's store the inbound requested format
    # We need to simplify the format call to the backend
    # so that we get data we can manipulate
    if "_format" in query_params:
        req_format = query_params["_format"]
    elif "format" in query_params:
        req_format = query_params["format"]
    else:
        req_format = "html"
    #
    # logger.debug("Saving requested format:%s" % req_format)

    return req_format


def build_querystring(query_dict):
    """
    Manipulate the Query String to a decoded format

    :param query_dict:
    :return: query_out
    """

    # logger.debug("Query DICT:%s" % query_dict)

    query_out = "?"
    for k, v in query_dict.items():
        query_add = ("%s=%s&" % (k, v))
        query_out = query_out + query_add

    # logger.debug("Result:%s" % query_out)
    if query_out == "?":
        return None
    else:
        return query_out[:-1]


def add_key_to_fhir_url(fhir_url, resource_type, key=""):
    """
    Append the key + / to fhir_url, unless it is already there
    :param fhir_url:
    :param resource_type:
    :param key:
    :return: fhir_url
    """
    if fhir_url.endswith(resource_type + '/'):
        # we need to make sure we don't specify resource_type twice in URL
        if key.startswith(resource_type + '/'):
            key = key.replace(resource_type + '/', '')

    if key + '/' in fhir_url:
        pass
        # logger.debug("%s/ already in %s" % (key, fhir_url))
    else:
        # logger.debug("adding %s/ to fhir_url: %s" % (key, fhir_url))
        fhir_url += key + '/'

    return fhir_url


def fhir_call_type(interaction_type, fhir_url, vid=None):
    """
    Append a call type to the fhir_url.
    Call this before adding an identifier.
    :param interaction_type:
    :param fhir_url:
    :param vid:
    :return: pass_to
    """

    if interaction_type == 'vread':
        pass_to = fhir_url + '_history' + '/' + vid
    elif interaction_type == '_history':
        pass_to = fhir_url + '_history'
    else:  # interaction_type == 'read':
        pass_to = fhir_url

    return pass_to


def get_div_from_json(raw_json):
    """
    Get the div from a json resource
    :param raw_json:
    :return: div_text
    """

    div_text = []
    if raw_json:
        for k, v in raw_json.items():
            # print("k:%s" % k)
            if k == "text":
                if 'div' in v:
                    # print("TEXT FOUND:%s [%s]" % (k, v))
                    div_text.append(v['div'])

    return div_text
