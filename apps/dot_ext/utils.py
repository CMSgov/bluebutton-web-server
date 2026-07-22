import logging
import os
import re
from base64 import b64decode
from http import HTTPStatus

import jwt
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpRequest
from django.http.response import JsonResponse
from oauth2_provider.models import (
    AccessToken,
    RefreshToken,
    get_application_model,
)
from oauthlib.oauth2.rfc6749.errors import (
    InvalidClientError,
    InvalidGrantError,
    InvalidRequestError,
)

from apps.authorization.models import DataAccessGrant
from apps.constants import (
    APPLICATION_ONE_TIME_REFRESH_NOT_ALLOWED_MESG,
    APPLICATION_TEMPORARILY_INACTIVE,
    APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_EXPIRED_MESG,
    AUDIT_EVENT_SCOPE,
    AUDIT_EVENT_SEARCH_SCOPE,
    HHS_SERVER_LOGNAME_FMT,
    REFRESH_TOKEN,
)
from apps.dot_ext.constants import APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_NOT_FOUND_MESG
from apps.dot_ext.models import AccessTokenExtension, Application, AuthFlowTracking
from apps.versions import VersionNotMatched, Versions

User = get_user_model()

log = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))

CLIENT_ID_PATTERN = re.compile(r'[a-zA-Z0-9]{40}')


def validate_client_id(client_id: str) -> None:
    """Validate that a client_id matches the expected format (40 alphanumeric characters).

    Skips validation when TARGET_ENV is 'local' or unset.

    Raises:
        InvalidClientError: If the client_id does not match the expected pattern.
    """
    env = os.environ.get('TARGET_ENV', 'local')
    if env in ('local', 'codebuild'):
        return
    if not CLIENT_ID_PATTERN.fullmatch(client_id):
        raise InvalidClientError(
            description='Invalid client_id format',
            status_code=HTTPStatus.BAD_REQUEST,
        )


def get_oauth_param(request: HttpRequest, parameter: str, fallback_session_parameter: str = None) -> str | None:
    """Resolve an OAuth parameter from GET, then session, then session['oauth_params']. If those are not available,
    use request.POST.

    Args:
        request: Django HttpRequest object
        parameter: The parameter name to look up
        fallback_session_parameter: Optional alternate session key to try (e.g. 'auth_client_id' for 'client_id')

    Returns:
        The first truthy value found, or None
    """
    result = request.GET.get(parameter) or request.session.get(parameter)
    if not result and fallback_session_parameter:
        result = request.session.get(fallback_session_parameter)
    if not result and request.POST.get(parameter):
        result = request.POST.get(parameter)

    return result or request.session.get('oauth_params', {}).get(parameter)


def remove_application_user_pair_tokens_data_access(
    application, user, delete_data_access_grant: bool, delete_access_tokens: bool
):
    """
    Utility function to revoke and delete current application/user pair
    access_token, refresh_token and DataAccessGrant records.

    This is to be used related to changes in a choice for a beneficiary
    to not share or an application to not require demographic scopes.

    This ensures that previously created tokens, with full scopes, can not
    be used when there is a change.

    RETURN:
        access_token_delete_cnt = Access tokens deleted.
        refresh_token_delete_cnt = Refresh tokens deleted.
        data_access_grant_delete_cnt = DataAccessGrant records deleted (0 or 1).

    CALLED FROM:
        apps.dot_ext.views.authorization.authorization.AuthorizationView.form_valid()
    """
    data_access_grant_delete_cnt = 0
    with transaction.atomic():
        if delete_access_tokens:
            # Get count of access tokens to be deleted and actually delete them
            access_token_delete_cnt = AccessToken.objects.filter(application=application, user=user).delete()[0]
        else:
            # Get count of access tokens to be deleted.
            access_token_delete_cnt = AccessToken.objects.filter(application=application, user=user).count()

        # Delete DataAccessGrant record.
        # NOTE: This also revokes/deletes access and only revokes refresh tokens via signal function.
        if delete_data_access_grant:
            data_access_grant_delete_cnt = DataAccessGrant.objects.filter(
                application=application, beneficiary=user
            ).delete()[0]

        # Delete refresh token records
        refresh_token_delete_cnt = RefreshToken.objects.filter(application=application, user=user).delete()[0]

    return (
        data_access_grant_delete_cnt,
        access_token_delete_cnt,
        refresh_token_delete_cnt,
    )


def get_application_from_meta(request) -> Application | None:
    """
    Utility function to application from auth header.
    This method will pull either the access token
    or the client id from the header and use that
    value to retrieve the application.
    RETURN:
        application or None
    """
    request_meta = getattr(request, 'META', None)
    client_id, ac = None, None
    Application = get_application_model()
    app = None
    if request_meta:
        auth_header = request_meta.get('HTTP_AUTHORIZATION', None)
        if not auth_header:
            auth_header = request_meta.get('Authorization', None)
        if auth_header:
            if 'Bearer' in auth_header:
                ac = AccessToken.objects.get(token=auth_header.split(' ')[1])
            else:
                encoded_credentials = auth_header.split(' ')[1]  # Removes 'Basic ' to isolate credentials
                decoded_credentials = b64decode(encoded_credentials).decode('utf-8').split(':')
                client_id = decoded_credentials[0]
    try:
        if client_id is not None:
            validate_client_id(client_id)
            app = Application.objects.get(client_id=client_id)
        elif ac is not None:
            app = Application.objects.get(id=ac.application_id)
    except Application.DoesNotExist:
        raise InvalidClientError(description='Application does not exist')
    return app


def get_application_from_data(request):
    """
    Utility function to get application from POST/GET data.
    This method will pull the client_id, access token,
    or refresh token from the request data and use that
    value to retrieve the application.
    RETURN:
        application or None
    """
    client_id, token, rt, app = None, None, None, None
    Application = get_application_model()

    # Try and get the application via `client_id`
    # If the client id comes in via GET or POST, we can try and look
    # up the application via the client_id. If we find it, return it.
    # If not, we have a bad request, because a client_id was present,
    # but malformed in some way.
    if request.GET.get('client_id'):
        client_id = request.GET.get('client_id')
    elif request.POST.get('client_id'):
        client_id = request.POST.get('client_id')

    if client_id:
        validate_client_id(client_id)

    if request.POST.get('client_assertion'):
        # for client credentials flow, we need to get the client_id from the client_assertion
        try:
            token = request.POST.get('client_assertion')
            auth_jwt = jwt.decode(token, options={'verify_signature': False})
            client_assertion_client_id = auth_jwt.get('iss')

            if client_id:
                if client_id != client_assertion_client_id:
                    raise InvalidRequestError(
                        description='client_id param did not match client_id in JWT',
                        status_code=HTTPStatus.BAD_REQUEST,
                    )
            else:
                client_id = client_assertion_client_id

            if client_id:
                validate_client_id(client_id)
        except jwt.PyJWTError:
            raise InvalidRequestError(
                description='Malformed client_assertion',
                status_code=HTTPStatus.BAD_REQUEST,
            )

    try:
        if client_id:
            app = Application.objects.get(client_id=client_id)
            return app
    except Application.DoesNotExist:
        raise InvalidClientError(
            description='Application does not exist (client_id)',
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Try via token
    # If we manage to find an access token, but then not an application, we
    # have a problem, and should return an error.
    if request.POST.get('token', None):
        try:
            token = AccessToken.objects.get(token=request.POST.get('token', None))
        except AccessToken.DoesNotExist:
            if request.POST.get('token_type_hint', None) == REFRESH_TOKEN:
                try:
                    token = RefreshToken.objects.get(token=request.POST.get('token', None))
                except RefreshToken.DoesNotExist:
                    raise InvalidClientError(
                        description='Token not found.',
                        status_code=HTTPStatus.BAD_REQUEST,
                    )
            else:
                raise InvalidClientError(
                    description='Token not found.',
                    status_code=HTTPStatus.BAD_REQUEST,
                )
    try:
        if token is not None:
            app = Application.objects.get(id=token.application_id)
            return app
    except Application.DoesNotExist:
        raise InvalidClientError(
            description='Application does not exist (token)',
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Try via refresh_token
    # Finally, if we have a refresh token, but cannot find an app, that's not good.
    if request.POST.get('refresh_token'):
        try:
            rt = RefreshToken.objects.get(token=request.POST.get('refresh_token', None))
        except RefreshToken.DoesNotExist:
            raise InvalidClientError(
                description='Refresh token not found.',
                status_code=HTTPStatus.BAD_REQUEST,
            )
    try:
        if rt is not None:
            app = Application.objects.get(id=rt.application_id)
            return app
    except Application.DoesNotExist:
        raise InvalidClientError(
            description='Application does not exist (refresh_token)',
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Return None if we get to this point, partially to match behavior expected in tests.
    return None


def get_application_from_request(request):
    meta_app = get_application_from_meta(request)
    data_app = get_application_from_data(request)
    if meta_app and data_app and meta_app != data_app:
        raise InvalidRequestError(
            description='different app in headers than in request data',
            status_code=HTTPStatus.BAD_REQUEST,
        )
    if meta_app is None:
        return data_app
    else:
        return meta_app


def validate_app_is_active(request: HttpRequest) -> Application:
    """
    Utility function to check that an application is an active, valid application.
    This method will pull the application from the request and then check the active flag and the
    data access grant (DA) validity.
    Args:
        request (HttpRequest): Django HttpRequest object

    Raises:
        InvalidClientError: Application can't refresh or isn't active
        InvalidGrantError: Could not find a corresponding DAG, or DAG has expired
        InvalidRequestError: Missing refresh token parameter

    Returns:
        Model: Application model
    """
    app = get_application_from_request(request)

    if not app:
        raise InvalidClientError('App id failed')

    # revoked access and expired auth period to a 401 error
    if app.active:
        # Is this for a token refresh request?
        post_grant_type = request.POST.get('grant_type', None)
        if post_grant_type == 'refresh_token':
            # A ONE_TIME token is not allowed to be refreshed.
            # In that instance, we raise an error that explicitly
            # indicates that the user must re-authenticate.
            # This is a FORBIDDEN error for the API consumer.
            if app.has_one_time_only_data_access():
                raise InvalidClientError(
                    description=APPLICATION_ONE_TIME_REFRESH_NOT_ALLOWED_MESG,
                    status_code=HTTPStatus.FORBIDDEN,
                )

            refresh_code = request.POST.get('refresh_token', None)
            try:
                refresh_token = RefreshToken.objects.get(token=refresh_code)
                dag = DataAccessGrant.objects.get(beneficiary=refresh_token.user, application=app)

                if dag:
                    # If we get a DAG, but it has expired, we pass back a message (again)
                    # saying the end user must re-authenticate.
                    if dag.has_expired():
                        # https://www.rfc-editor.org/rfc/rfc6750#section-3.1
                        # We will return a 401 (UNAUTHORIZED) because this is in keeping
                        # with the OAuth RFC.
                        raise InvalidGrantError(
                            description=APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_EXPIRED_MESG,
                            status_code=HTTPStatus.UNAUTHORIZED,
                        )
            except DataAccessGrant.DoesNotExist:
                # In the event that we cannot find a DAG, we don't want to pass back too much information.
                # We pass back a FORBIDDEN and a message saying as much (and, again, encouraging
                # reauthentication).
                raise InvalidGrantError(
                    description=APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_NOT_FOUND_MESG,
                    status_code=HTTPStatus.FORBIDDEN,
                )
            except RefreshToken.DoesNotExist:
                raise InvalidRequestError(
                    description='Missing refresh token parameter',
                    status_code=HTTPStatus.BAD_REQUEST,
                )
    else:
        raise InvalidClientError(
            description=APPLICATION_TEMPORARILY_INACTIVE.format(app.name),
            status_code=HTTPStatus.FORBIDDEN,
        )

    return app


def json_response_from_oauth2_error(error):
    """
    Given a oauthlib.oauth2.rfc6749.errors.* error this function
    returns a corresponding django.http.response.JsonResponse response
    """
    ret_data = {'status_code': error.status_code, 'error': error.error}

    # Add optional description
    if getattr(error, 'description', None):
        ret_data['error_description'] = error.description

    return JsonResponse(ret_data, status=error.status_code)


def get_api_version_number_from_url(url_path: str) -> int:
    """Utility function to extract what version of the API a URL is
    If there are multiple occurrences of 'v{{VERSION}} in a url path,
    only return the first one
    EX. /v2/o/authorize will return v2.

    Args:
        url_path (str): The url being called that we want to extract the api version

    Returns:
        Optional[str]: Returns a string of v2
    """
    match = re.search(r'/v(\d+)/', url_path, re.IGNORECASE)
    if match:
        version = int(match.group(1))
        if version in Versions.supported_versions():
            return version
        else:
            raise VersionNotMatched(f'{version} extracted from {url_path}')

    return Versions.NOT_AN_API_VERSION


def validate_latin_extended_string(text: str) -> bool:
    """Checks if a string has all values (and at least one value) that fall within ascii, latin supplement, and extended:
        https://en.wikipedia.org/wiki/Latin_Extended-A

    Args:
        text (str): the text to check

    Returns:
        bool: if all strings are encoded less than U+017F (383) and it is not empty
    """
    return all(ord(char) <= 383 for char in text) and bool(text)


def check_auth_tracking_and_create_access_token_extension(
    prior_include_samhsa: bool,
    code: str,
    grant_type: str,
    token: AccessToken,
    prior_part_d_eob_only: bool,
) -> None:
    """Retrieve a record from the AuthFlowTracking table, if available, for the code being used in the authorization
    or refresh request

    Args:
        prior_include_samhsa (bool): The value the prior access_token_extension record had for include_samhsa
        code (str): The code for the auth or refresh request, used to retrieve AuthFlowTracking record
        grant_type (str): Grant type of the call to TokenView.post
        token (AccessToken): The access token that was generated
        prior_part_d_eob_only (bool): The prior part_d_eob_only for the previously existing AccessTokenExtension. Used
        to make sure that if the app setting has changed, that the prior part_d_eob_only value is preserved on a token
        refresh
    """
    include_samhsa = True

    # Try to retrieve the value from the AuthFlowTracking model based on the code
    # If we do retrieve one, set include_samhsa to that value, gathered from the v3 permissions screen
    # and afterwards delete the record so the table doesn't grow overly large. If there is no record,
    # continue with the execution
    if grant_type != 'refresh_token' and code:
        try:
            auth_flow_tracking = AuthFlowTracking.objects.get(code=code)
            include_samhsa = auth_flow_tracking.include_samhsa
            auth_flow_tracking.delete()

        except AuthFlowTracking.DoesNotExist:
            # If the AuthFlowTracking object does not exist, go with the default include_samhsa of True
            pass

    if grant_type == 'refresh_token':
        include_samhsa = prior_include_samhsa

    AccessTokenExtension.objects.get_or_create(
        access_token=token, include_samhsa=include_samhsa, part_d_eob_only=prior_part_d_eob_only
    )


def check_can_token_scope_for_audit_event_scopes(scope: str) -> str:
    """Check the token being created as a result of a CAN call for AuditEvent scopes.
    Currently, we only want to apply patient/AuditEvent.rs as a scope. If .r or .s are on
    the token scope, remove those. If patient/AuditEvent.rs is not on the scope, add it.

    Args:
        scope (str): The scope parameter that was passed to the CAN token call

    Returns:
        str: The scope parameter after AuditEvent checks have been performed
    """

    audit_event_read_pattern = r'patient/AuditEvent\.r\b'

    # We need a different strategy for replacing patient/AuditEvent.r as it is a substring
    # of the patient/AuditEvent.rs scope. That is why regex is used.
    if re.search(audit_event_read_pattern, scope):
        scope = re.sub(audit_event_read_pattern, '', scope)

    if AUDIT_EVENT_SEARCH_SCOPE in scope:
        log.info('patient/AuditEvent.s scope requested for client_credentials call, removing it')
        scope = scope.replace(AUDIT_EVENT_SEARCH_SCOPE, '')

    if AUDIT_EVENT_SCOPE not in scope:
        log.info('patient/AuditEvent.rs scope not requested for client_credentials call, adding it')
        scope += ' ' + AUDIT_EVENT_SCOPE

    # Ensure any extra spaces are filtered
    return ' '.join(scope.split())
