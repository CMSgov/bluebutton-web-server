import json
import logging

from collections import OrderedDict
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse

from apps.fhir.fhir_core.models import SupportedResourceType

logger = logging.getLogger('hhs_server.%s' % __name__)

ERROR_CODE_LIST = [301, 302, 400, 401, 402, 403, 404, 500, 501, 502, 503, 504]

SESSION_KEY = 'BBF_search_session'


def kickout_301(reason, status_code=301):
    """ 301 Moved Permanently """
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
    """ 503 Gateway Timeour """
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


def error_status(r, status_code=404, reason='undefined error occured'):
    """
    Generate an error page
    based on fhir.utils.kickout_xxx
    :param r:
    :param status_code:
    :param reason:
    :return:
    """
    error_detail = r.text
    if settings.DEBUG:
        if r.text[0] == '<':
            error_detail = 'xml:'
            error_detail += r.text
        else:
            error_detail = r.json()

    if reason == 'undefined error occured':
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
            kickout_301(reason)
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
        'vid': vid
    }

    """
    now = datetime.now()
    then = now + timedelta(minutes=settings.FHIR_SERVER_CONF['SEARCH_EXPIRY'])
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
        'vid': vid
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
    """ Check for _format=xml or _format=json or other """

    parameter_search = search_parm.lower()
    if '_format=xml' in parameter_search:
        fmt = 'xml'
    elif '_format=json' in parameter_search:
        fmt = 'json'
    else:
        fmt = ''

    return fmt


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
