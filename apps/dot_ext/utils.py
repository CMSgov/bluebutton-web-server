from base64 import b64decode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http.response import JsonResponse
from oauth2_provider.models import AccessToken, RefreshToken, get_application_model
from oauthlib.oauth2.rfc6749.errors import InvalidClientError

from apps.authorization.models import DataAccessGrant


User = get_user_model()


def remove_application_user_pair_tokens_data_access(application, user):
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
    with transaction.atomic():
        # Get count of access tokens to be deleted.
        access_token_delete_cnt = AccessToken.objects.filter(
            application=application, user=user
        ).count()

        # Delete DataAccessGrant record.
        # NOTE: This also revokes/deletes access and only revokes refresh tokens via signal function.
        data_access_grant_delete_cnt = DataAccessGrant.objects.filter(
            application=application, beneficiary=user
        ).delete()[0]

        # Delete refresh token records
        refresh_token_delete_cnt = RefreshToken.objects.filter(
            application=application, user=user
        ).delete()[0]

    return (
        data_access_grant_delete_cnt,
        access_token_delete_cnt,
        refresh_token_delete_cnt,
    )


def get_application_from_meta(request):
    """
    Utility function to application from auth header.
    This method will pull either the access token
    or the client id from the header and use that
    value to retrieve the application.
    RETURN:
        application or None
    """
    request_meta = getattr(request, "META", None)
    client_id, ac = None, None
    Application = get_application_model()
    app = None
    if request_meta:
        auth_header = request_meta.get("HTTP_AUTHORIZATION", None)
        if not auth_header:
            auth_header = request_meta.get("Authorization", None)
        if auth_header:
            if 'Bearer' in auth_header:
                ac = AccessToken.objects.get(token=auth_header.split(' ')[1])
            else:
                encoded_credentials = auth_header.split(' ')[1]  # Removes "Basic " to isolate credentials
                decoded_credentials = b64decode(encoded_credentials).decode("utf-8").split(':')
                client_id = decoded_credentials[0]
    try:
        if client_id is not None:
            app = Application.objects.get(client_id=client_id)
        elif ac is not None:
            app = Application.objects.get(id=ac.application_id)
    except Application.DoesNotExist:
        pass
    return app


def validate_app_is_active(request):
    """
    Utility function to check that an application
    is an active, valid application.
    This method will pull the application from the
    request and then check the active flag.
    RETURN:
        application or None
    """
    app = get_application_from_meta(request)
    if not app:
        app = get_application_from_data(request)

    if app and app.active:
        # Is this for a token refresh request?
        post_grant_type = request.POST.get("grant_type", None)
        if post_grant_type == "refresh_token":
            # Check for application ONE_TIME type where token refresh is not allowed.
            if app.has_one_time_only_data_access():
                raise InvalidClientError(
                    description=settings.APPLICATION_ONE_TIME_REFRESH_NOT_ALLOWED_MESG
                )

            # Check if data access grant is expired for THIRTEEN_MONTH app type?
            if hasattr(request, 'user'):
                if not request.user.is_anonymous:
                    try:
                        dag = DataAccessGrant.objects.get(
                            beneficiary=request.user,
                            application=app
                        )

                        if dag:
                            if dag.has_expired():
                                raise InvalidClientError(
                                    description=settings.APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_EXPIRED_MESG
                                )

                    except DataAccessGrant.DoesNotExist:
                        pass
    elif app and not app.active:
        raise InvalidClientError(
            description=settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name)
        )

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
    client_id, ac, rt, app = None, None, None, None
    Application = get_application_model()

    if request.GET.get("client_id", None) is not None:
        client_id = request.GET.get("client_id", None)
    elif request.POST.get("client_id", None):
        client_id = request.POST.get("client_id", None)
    elif request.POST.get("token", None):
        # introspect
        ac = AccessToken.objects.get(token=request.POST.get("token", None))
    elif request.POST.get("refresh_token"):
        rt = RefreshToken.objects.get(token=request.POST.get("refresh_token", None))
    try:

        if client_id is not None:
            app = Application.objects.get(client_id=client_id)
        elif ac is not None:
            app = Application.objects.get(id=ac.application_id)
        elif rt is not None:
            app = Application.objects.get(id=rt.application_id)

    except Application.DoesNotExist:
        pass
    return app


def json_response_from_oauth2_error(error):
    """
    Given a oauthlib.oauth2.rfc6749.errors.* error this function
    returns a corresponding django.http.response.JsonResponse response
    """
    ret_data = {"status_code": error.status_code, "error": error.error}

    # Add optional description
    if getattr(error, "description", None):
        ret_data["error_description"] = error.description

    return JsonResponse(ret_data, status=error.status_code)
