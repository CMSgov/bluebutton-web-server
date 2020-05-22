from rest_framework.exceptions import NotFound, ValidationError, APIException
from rest_framework import status
from .models import Fhir_Response

FHIR_RS_TYPE="resourceType"
FHIR_OP_OUTCOME="OperationOutcome"
FHIR_OP_OUTCOME_ISSUE="issue"
FHIR_OP_OUTCOME_DIAGNOSTICS="diagnostics"

BAD_REQ_ERRORS = [
    "Unsupported ID pattern",
]

def is_bad_request(json_data):
    """
    helper to determine nature of backend error, hueristcally.
    """
    if type(json_data) is dict and \
        json_data.get(FHIR_RS_TYPE) == FHIR_OP_OUTCOME:
            for issue in json_data.get(FHIR_OP_OUTCOME_ISSUE):
                if match_bad_req_err(issue.get(FHIR_OP_OUTCOME_DIAGNOSTICS)):
                    return True

def match_bad_req_err(msg):
    for e in BAD_REQ_ERRORS:
        if e in msg:
            return True

def filter_backend_response(response: Fhir_Response) -> APIException:
    """
    TODO: This should be more specific (original comment before BB2-128)
    
    BB2-128: map BFD coarse grained 500 error on FHIR read / search etc. with malformed
    parameters, e.g. an invalid regex pattern etc., to a FHIR compliant http code.
    this mapping is desirable since back end fhir server may not always response with
    FHIR compliant http error code.
      
    """
    err_ret: APIException = None

    if response.status_code == 404:
        err_ret = NotFound(detail='The requested resource does not exist')
    else:
        if response.status_code >= 300:
            if response.status_code == 500:
                # json_data = None
                # try:
                #     json_data = r.json()
                # except Exception as ex:
                #     pass

                if is_bad_request(response.json):
                    err_ret = ValidationError(response.json)
            ## catch rest (>=300 but not 500)                    
            err_ret = UpstreamServerException(detail='An error occurred contacting the upstream server')
    
    return err_ret


class UpstreamServerException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
