import logging
import datetime
import uuid
import binascii
from django.conf import settings
from apps.fhir.bluebutton.utils import (get_ip_from_request,
                                        get_user_from_request,
                                        get_access_token_from_request)
from apps.accounts.models import get_user_id_salt
from django.utils.crypto import pbkdf2
from oauth2_provider.models import AccessToken


logger = logging.getLogger('performance.%s' % __name__)

##############################################################################
#
# Request time logging middleware
# https://djangosnippets.org/snippets/1826/
#
##############################################################################


class RequestTimeLoggingMiddleware(object):
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
    def log_message(request, tag, message=''):
        """Audit Log message to stderr/INFO.

        Logs message about `request'/'response' pair with a `tag' (a string, 10
        characters or less if possible). This is in a single-line JSON format.


        The JSON log format contians the following fields:
            - tag = The 10-char or less logging type. audittrail for request/response pairs.
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

        # Save request data else log request/response pair info.
        dt = datetime.datetime.utcnow()
        if not hasattr(request, '_logging_uuid'):
            request._logging_uuid = uuid.uuid1()
            request._logging_start_dt = dt
            request._logging_pass = 0
        else:
            # Gather logging details.
            access_token = get_access_token_from_request(request)

            if AccessToken.objects.filter(token=access_token).exists():
                at = AccessToken.objects.get(token=access_token)
                app_name = str(at.application.name)
                app_id = str(at.application.id)
                dev_id = str(at.application.user.id)
                dev_name = str(at.application.user)
                access_token_hash = binascii.hexlify(pbkdf2(access_token, get_user_id_salt(),
                                                            settings.USER_ID_ITERATIONS)).decode("ascii")
            else:
                app_name = ""
                app_id = ""
                dev_id = ""
                dev_name = ""
                access_token_hash = ""

            log_fmt = '{ \"tag\" : \"%-10s\", \"start_time\" : \"%s\", \"end_time\" : \"%s\", \"request_uuid\" : \"%s\", ' + \
                      '\"path" : \"%s\", \"response_code\" : \"%s\", \"size\" : \"%s\", \"location\" : \"%s\", ' + \
                      '\"user\" : \"%s\",\"ip_addr\" : \"%s\", \"access_token_hash\" : \"%s\", ' + \
                      '\"app_name\" : \"%s\", \"app_id\" : \"%s\", \"dev_name\" : \"%s\", \"dev_id\" : \"%s\" }'

            logger.info(log_fmt % (tag, request._logging_start_dt.timestamp(), dt.timestamp(), request._logging_uuid,
                                   request.path, str(request._logging_response_code),
                                   str(request._logging_response_size) if hasattr(request,
                                                                                  '_logging_response_size') else "",
                                   str(request._logging_response_location) if hasattr(request,
                                                                                      '_logging_response_location') else "",
                                   get_user_from_request(request), get_ip_from_request(request), access_token_hash,
                                   app_name, app_id, dev_name, dev_id))

        request._logging_pass += 1

    def process_request(self, request):
        self.log_message(request, 'request ')

    def process_response(self, request, response):
        s = getattr(response, 'status_code', 0)
        request._logging_response_code = s
        request._logging_response_location = ""

        if s in (300, 301, 302, 307):
            request._logging_response_location = response.get('Location', '?')
        elif response.content:
            request._logging_response_size = len(response.content)

        self.log_message(request, 'audittrail', "")
        return response
