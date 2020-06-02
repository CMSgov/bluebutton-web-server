from rest_framework.exceptions import NotFound, APIException
from rest_framework import status
from requests import Response
from .models import Fhir_Response


def process_error_response(response: Fhir_Response) -> APIException:
    """
    TODO: This should be more specific (original comment before BB2-128)
    BB2-128: map BFD coarse grained 500 error to 502 (backward compatible),
    attach FHIR response as details such that BB2 API consumer could act on
    the response depend on nature of the response.
    """
    err: APIException = None
    r: Response = response.backend_response
    if response.status_code >= 300:
        bfd_err = {'FHIR response status_code': response.status_code}
        bfd_err.update({'fhir response content': r.content})
        if response.status_code == 404:
            bb2_err = {'Error': response.status_code, 'message': 'The requested resource does not exist'}
            err = NotFound(detail={**bb2_err, **bfd_err})
        else:
            bb2_err = {'Error': 502, 'message': 'An error occurred contacting the upstream server'}
            err = UpstreamServerException(detail={**bb2_err, **bfd_err})
    return err


class UpstreamServerException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
