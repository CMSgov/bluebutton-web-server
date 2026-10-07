import logging

from oauthlib.oauth2.rfc6749.errors import TokenExpiredError

from apps.constants import HHS_SERVER_LOGNAME_FMT
from apps.testclient.constants import ResponseErrors

logger = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))


class TestClientTokenExpiredMiddleware:
    """Turns an expired testclient session token into a handled 401 instead of a 500.

    This is the single place that handles TokenExpiredError (raised by requests_oauthlib
    when a FHIR call is made with an expired access token) so individual testclient views
    (test_patient_vX, test_eob_vX, test_coverage_vX, etc.) don't each need to catch it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, TokenExpiredError):
            return None

        logger.warning('FHIR data call made with an expired access token.')
        if 'token' in request.session:
            del request.session['token']
        return ResponseErrors.TokenExpiredError()
