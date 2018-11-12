import logging
import datetime
import uuid
import hashlib
import json
from apps.fhir.bluebutton.utils import (get_ip_from_request,
                                        get_user_from_request,
                                        get_access_token_from_request)
from oauth2_provider.models import AccessToken
from django.utils.deprecation import MiddlewareMixin


audit = logging.getLogger('audit.%s' % __name__)


class RequestResponseLog(object):
    """Audit Log message to JSON string

    The JSON log format contians the following fields:
        - start_time = Unix Epoch format time of the request processed.
        - end_time = Unix Epoch format time of the response processed.
        - request_uuid = The UUID identifying the request.
        - path = The request.path.
        - response_code = The response status code.
        - size = Size in bytes of the response.content
        - location = Location (redirect) for 300,301,302,307 response codes.
        - user = Login user (or None) or OAuth2 API.
        - ip_addr = IP address of the request, account for the possibility of being behind a proxy.
        - access_token_hash = A hash of the access token.
        - app_name = Application name.
        - app_id = Application id.
        - dev_name = Developer user name.
        - dev_id = Developer user id.
    """

    request = None
    response = None

    def __init__(self, req, resp):
        self.request = req
        self.response = resp

    def __str__(self):
        # Create log message dict
        log_msg = {}
        log_msg['start_time'] = self.request._logging_start_dt.timestamp()
        log_msg['end_time'] = datetime.datetime.utcnow().timestamp()
        log_msg['request_uuid'] = str(self.request._logging_uuid)
        log_msg['path'] = self.request.path
        log_msg['response_code'] = getattr(self.response, 'status_code', 0)
        log_msg['size'] = ""
        log_msg['location'] = ""
        log_msg['app_name'] = ""
        log_msg['app_id'] = ""
        log_msg['dev_id'] = ""
        log_msg['dev_name'] = ""
        log_msg['access_token_hash'] = ""

        if log_msg['response_code'] in (300, 301, 302, 307):
            log_msg['location'] = self.response.get('Location', '?')
        elif getattr(self.response, 'content', False):
            log_msg['size'] = len(self.response.content)

        log_msg['user'] = str(get_user_from_request(self.request))
        log_msg['ip_addr'] = get_ip_from_request(self.request)

        access_token = getattr(self.request, 'auth', get_access_token_from_request(self.request))

        if AccessToken.objects.filter(token=access_token).exists():
            at = AccessToken.objects.get(token=access_token)
            log_msg['app_name'] = at.application.name
            log_msg['app_id'] = at.application.id
            log_msg['dev_id'] = at.application.user.id
            log_msg['dev_name'] = str(at.application.user)
            try:
                log_msg['org_name'] = at.application.user.user_profile.organization_name
            except Exception:
                pass
            log_msg['access_token_hash'] = hashlib.sha256(str(access_token).encode('utf-8')).hexdigest()

        return(json.dumps(log_msg))


##############################################################################
#
# Request time logging middleware
# https://djangosnippets.org/snippets/1826/
#
##############################################################################


class RequestTimeLoggingMiddleware(MiddlewareMixin):
    """Middleware class logging request time to stderr.

    This class can be used to measure time of request processing
    within Django.  It can be also used to log time spent in
    middleware and in view itself, by putting middleware multiple
    times in INSTALLED_MIDDLEWARE.

    Static method `log_message' may be used independently of the
    middleware itself, outside of it, and even when middleware is not
    listed in INSTALLED_MIDDLEWARE.
    """

    @staticmethod
    def log_message(request, response):
        audit.info(RequestResponseLog(request, response))
        request._logging_pass += 1

    def process_request(self, request):
        request._logging_uuid = uuid.uuid1()
        request._logging_start_dt = datetime.datetime.utcnow()
        request._logging_pass = 1

    def process_response(self, request, response):
        self.log_message(request, response)
        return response
