from rest_framework.exceptions import NotFound, APIException
from rest_framework import status
from requests import Response
from requests.exceptions import JSONDecodeError
from apps.fhir.bluebutton.models import Fhir_Response


def process_error_response(response: Fhir_Response) -> APIException:
    """
    Process errors coming from FHIR endpoints.
    * All 2XX errors pass through as-is.
    * All 3XX errors are wrapped and become a 502
    * All 4XX errors are wraped and become a 400
        * All 4XX errors get additional diagnostics attached
        * Except 404, which remains a NotFound
    * All 5XX errors are wrapped and become a 502
    """
    err: APIException = None
    r: Response = response.backend_response
    if response.status_code is None:
        # This should be impossible.
        msg = 'No status code from the upstream server'
        err = UpstreamServerException(msg)
        return err
    elif response.status_code < 300:
        # If we're returning a "good" status, short circuit and
        # return a None value.
        return err
    elif response.status_code == 404:
        err = NotFound('Not found.')
        return err
    elif response.status_code >= 300 and response.status_code < 400:
        # If we are being redirected, that's unexpected from our FHIR servers.
        # Wrap the error and return
        msg = 'An error occurred contacting the upstream server'
        err = UpstreamServerException(msg)
        return err
    elif response.status_code >= 400 and response.status_code < 500:
        # In the 400-range, we will return those to the client.
        # We'll try and parse the JSON. If we can, we'll formulate a
        # more detailed message. If we can't, we'll return a default
        # wrapped response.
        msg = 'An error occurred contacting the upstream server'
        err = UpstreamServerException(msg)
        try:
            json = r.json()
            if json is not None:
                issues = json.get('issue')
                issue = issues[0] if issues else None
                diagnostics = issue.get('diagnostics') if issue else None
                if diagnostics is not None:
                    err = BadRequestToBackendError("{}:{}".format(msg, diagnostics))
        except JSONDecodeError:
            # Do nothing here; fall through and return `err`
            pass
        return err
    elif response.status_code >= 500:
        # Anything that is a 500-class error from upstream becomes a 502
        # as we propagate it forward.
        msg = 'A failure occurred contacting the upstream server'
        err = UpstreamServerException(msg)
        return err
    else:
        # Fallthrough
        pass

    # Our default is to return our None-type error response
    # However, this fallthrough is unlikely/cannot be reached.
    return err


class UpstreamServerException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY


class BadRequestToBackendError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
