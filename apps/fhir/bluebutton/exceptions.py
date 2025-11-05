from rest_framework.exceptions import NotFound, APIException
from rest_framework import status
from requests import Response
from requests.exceptions import JSONDecodeError
from .models import Fhir_Response


def process_error_response(response: Fhir_Response) -> APIException:
    """
    Process errors coming from FHIR endpoints.
    All status codes in 400s except 404 get wrapped in
    BadRequestError with diagnostics message attached if found.
    If not found, Generic UpstreamServerException will be returned.
    404 returns NotFound error.
    500 messages will return generic message with no diagnostics.
    """
    err: APIException = None
    r: Response = response.backend_response
    if response.status_code >= 300:
        if response.status_code == 404:
            err = NotFound('Not found.')
        else:
            msg = 'An error occurred contacting the upstream server'
            err = UpstreamServerException(msg)
            if response.status_code in range(400, 500):
                try:
                    json = r.json()
                    if json is not None:
                        issues = json.get('issue')
                        issue = issues[0] if issues else None
                        diagnostics = issue.get('diagnostics') if issue else None
                        if diagnostics is not None:
                            err = BadRequestToBackendError("{}:{}".format(msg, diagnostics))
                except JSONDecodeError:
                    pass
    return err


class UpstreamServerException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY


class BadRequestToBackendError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
