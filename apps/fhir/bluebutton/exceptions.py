from rest_framework.exceptions import NotFound, APIException
from rest_framework import status
from requests import Response
from requests.exceptions import JSONDecodeError
from .models import Fhir_Response

# 1xx informational response – the request was received, continuing process
# 2xx successful – the request was successfully received, understood, and accepted
# 3xx redirection – further action needs to be taken in order to complete the request
# 4xx client error – the request contains bad syntax or cannot be fulfilled
# 5xx server error – the server failed to fulfil an apparently valid request

def process_error_response(response: Fhir_Response) -> APIException:
    """ Need to be revised to new handling logic
    Process errors coming from FHIR endpoints.
    All status codes in 400s except 404 get wrapped in
    BadRequestError with diagnostics message attached if found.
    If not found, Generic UpstreamServerException will be returned.
    404 returns NotFound error.
    500 messages will return generic message with no diagnostics.
    """
    """
    Process errors coming from FHIR endpoints.
    Response with 404: throw NOTFOUND
    Any backend response which is a FHIR OperationOutcome will be passed through.
    For anything else, A UpstreamServerException will be returned with HTTP code 502.
    """
    if response.status_code in range(200, 400):
        # 2xx, 3xx - return to caller real quick
        return None
    else:
        err: APIException = None
        r: Response = response.backend_response
        if response.status_code == 404:
            # not found is not bad gateway
            err = NotFound('The requested resource does not exist')
        elif (response.status_code in range(400, 600) and
              not _is_operation_outcome(r)):
            # only back end response with 4xx, 5xx and the payload is not FHIR OperationOutcome
            # are treated as bad gateway
            # TODO: add more back end response content to the BAD GATEWAY message?
            # it helps trouble shooting, concern: would there be PII/PHI/sensitive info in the back end response? 
            err = UpstreamServerException('An error occurred contacting the upstream server')
        else:
            # 1xx - rare case, proceed to caller
            pass
        return err


class UpstreamServerException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY

#
# class BadRequestToBackendError(APIException):
#     status_code = status.HTTP_400_BAD_REQUEST
#

# helper to check if the response is a FHIR OperationOutcome
def _is_operation_outcome(r: Fhir_Response):
    result = False
    try:
        json = r.json()
        result = (json is not None
                  and json.get('resourceType') is not None
                  and json.get('resourceType') == 'OperationOutcome')
    except JSONDecodeError:
        # the body is not a json
        # TODO: consider debug logging the body content (e.g. a html string)
        # to help trouble shooting
        pass
    return result