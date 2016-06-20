import json
import logging

from collections import OrderedDict

from django.conf import settings
from django.http import HttpResponse

from apps.fhir.server.models import SupportedResourceType
from apps.fhir.bluebutton.models import ResourceTypeControl


logger = logging.getLogger('hhs_server.%s' % __name__)


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
    oo['resourceType']= 'OperationOutcome'
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
    oo['resourceType']= 'OperationOutcome'
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
    oo['resourceType']= 'OperationOutcome'
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
    oo['resourceType']= 'OperationOutcome'
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
            reason = 'You are not authorised to access this page. Do you need to login?'
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
