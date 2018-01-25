import json
import logging

from collections import OrderedDict
from django.conf import settings
from django.http import HttpResponse
from apps.fhir.server.models import SupportedResourceType


logger = logging.getLogger('hhs_server.%s' % __name__)


def kickout_301(reason, status_code=301):
    """ 301 Moved Permanently """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason]
    return HttpResponse(json.dumps(response),
                        status=status_code,
                        content_type='application/json')


def kickout_302(reason, status_code=302):
    """ 302 Temporarily Moved """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason]
    return HttpResponse(json.dumps(response),
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
    return HttpResponse(json.dumps(oo),
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
    return HttpResponse(json.dumps(oo),
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
    return HttpResponse(json.dumps(oo),
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
    return HttpResponse(json.dumps(oo),
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
    return HttpResponse(json.dumps(oo),
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
    return HttpResponse(json.dumps(oo),
                        status=status_code,
                        content_type='application/json')


def kickout_501(reason, status_code=501):
    """ 501 Not Implemented """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason, 'Not Implemented']
    return HttpResponse(json.dumps(response),
                        status=status_code,
                        content_type='application/json')


def kickout_502(reason, status_code=502):
    """ 502 Bad Gateway """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason, 'Bad Gateway']
    return HttpResponse(json.dumps(response),
                        status=status_code,
                        content_type='application/json')


def kickout_503(reason, status_code=503):
    """ 503 Gateway Timeout """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason, 'Gateway Timeout']
    return HttpResponse(json.dumps(response),
                        status=status_code,
                        content_type='application/json')


def kickout_504(reason, status_code=504):
    """ 504 Gateway Timeout """
    response = OrderedDict()
    response['code'] = status_code
    response['errors'] = [reason, 'Gateway Timeout']
    return HttpResponse(json.dumps(response),
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
    except Exception:
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

    return HttpResponse(json.dumps(response),
                        status=status_code,
                        content_type='application/json')


def check_lcase_list_item(list_value, check_for):
    """ search_param is a dict with each value as a list
        go through list to check for value. comparing as lowercase
     """

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
            return check_for

    return None


def strip_format_for_back_end(pass_params):
    updated_parameters = OrderedDict()
    for k in pass_params:
        if k.lower() == "_format":
            pass
        elif k.lower() == "format":
            pass
        else:
            updated_parameters[k] = pass_params[k]

    updated_parameters["_format"] = "json"
    return updated_parameters


def get_content_type(response):
    """ Check response headers for Content-Type
        expected options:
        application/json+fhir;charset=UTF-8
        application/xml+fhir;charset=UTF-8

    """
    if response.status_code >= 300:
        return error_status(response, response.status_code)
    else:
        result = OrderedDict()
        result['Content-Type'] = response.headers.get("Content-Type")
        return result


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
