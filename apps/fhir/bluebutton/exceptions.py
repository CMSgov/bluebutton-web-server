from rest_framework.exceptions import NotFound, APIException
from rest_framework import status
from requests import Response
from .models import Fhir_Response


def process_error_response(response: Fhir_Response) -> APIException:
    """
    TODO: This should be more specific (original comment before BB2-128)
    BB2-128: check FHIR response: if error is "IllegalArgumentException: Unsupported ID pattern..."
    then append the error to the general error message: 'An error occurred contacting the upstream server'
    """
    err: APIException = None
    r: Response = response.backend_response
    if response.status_code >= 300:
        if response.status_code == 404:
            err = NotFound('The requested resource does not exist')
        else:
            detail = 'An error occurred contacting the upstream server'
            if response.status_code == 500:
                json = None
                try:
                    json = r.json()
                except Exception:
                    pass
                if json is not None:
                    issues = json.get('issue')
                    issue = issues[0] if issues else None
                    diagnostics = issue.get('diagnostics') if issue else None
                    if diagnostics is not None and "Unsupported ID pattern" in diagnostics:
                        detail = detail + ": " + diagnostics
            err = UpstreamServerException(detail)
    return err


class UpstreamServerException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
