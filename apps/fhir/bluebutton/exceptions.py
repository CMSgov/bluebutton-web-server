from rest_framework.exceptions import NotFound, ValidationError, APIException
from rest_framework import status
from requests import Response
from .models import Fhir_Response

BAD_REQ_ERRORS = [
    "Unsupported ID pattern",
    "IllegalArgumentException",
]

FHIR_RS_TYPE = "resourceType"
FHIR_OP_OUTCOME = "OperationOutcome"
FHIR_OP_OUTCOME_ISSUE = "issue"
FHIR_OP_OUTCOME_DIAGNOSTICS = "diagnostics"


def match_bad_req_err_msg(msg):
    for e in BAD_REQ_ERRORS:
        if e.lower() in msg.lower():
            return True


def process_error_response(response: Fhir_Response) -> APIException:
    """
    TODO: This should be more specific (original comment before BB2-128)
    BB2-128: map BFD coarse grained 500 error on FHIR read / search etc. with malformed
    parameters, e.g. an invalid regex pattern etc., to a FHIR compliant http code.
    this mapping is desirable since back end fhir server may not always response with
    FHIR compliant http error code.

    """
    err: APIException = None
    if response.status_code == 404:
        err = NotFound(detail='The requested resource does not exist')
    else:
        r: Response = response.backend_response
        json_data = None
        if response.status_code >= 300:
            if response.status_code == 500:
                if r is not None:
                    try:
                        json_data = r.json()
                    except ValueError as ve:
                        pass

                    if type(json_data) is dict and json_data.get(FHIR_RS_TYPE) == FHIR_OP_OUTCOME:
                        for issue in json_data.get(FHIR_OP_OUTCOME_ISSUE):
                            if match_bad_req_err_msg(issue.get(FHIR_OP_OUTCOME_DIAGNOSTICS)):
                                bfd_err = {'fhir server status code': response.status_code}
                                err = ValidationError({**bfd_err, **json_data})

            # catch rest (>=300 and 500 except those treated as 400 bad request)
            if err is None:
                bb2_err = {'status_code': response.status_code, 'message': 'An error occurred contacting the upstream server'}
                bfd_err = {'fhir server status code': response.status_code}
                if json_data is not None:
                    bfd_err.update(json_data)
                err = UpstreamServerException(detail={**bb2_err, **bfd_err})
    return err


class UpstreamServerException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
