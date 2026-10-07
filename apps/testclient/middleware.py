import logging

from oauthlib.oauth2.rfc6749.errors import TokenExpiredError

from apps.constants import HHS_SERVER_LOGNAME_FMT
from apps.testclient.constants import FhirUnauthorizedError, ResponseErrors

logger = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))


class TestClientTokenExpiredMiddleware:
    """Turns a rejected/expired testclient session token into a handled 401 instead of a 500.

    This is the single place that handles both TokenExpiredError (raised client-side by
    requests_oauthlib when the session token's own expiry has passed) and FhirUnauthorizedError
    (raised by apps.testclient.views._get_fhir_data_as_json when the FHIR backend itself rejects
    the token)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, (TokenExpiredError, FhirUnauthorizedError)):
            return None

        logger.warning('FHIR data call made with a rejected or expired access token.')
        if 'token' in request.session:
            del request.session['token']
        return ResponseErrors.Unauthorized(getattr(exception, 'detail', None))
