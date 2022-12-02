from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http.response import JsonResponse
from oauth2_provider.models import AccessToken, RefreshToken, get_application_model
from oauthlib.oauth2.rfc6749.errors import InvalidClientError
from waffle import switch_is_active

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


def validate_app_is_active(request):
    Application = get_application_model()

    client_id, ac, app = None, None, None

    if request.GET.get("client_id", None) is not None:
        client_id = request.GET.get("client_id", None)
    elif request.POST.get("client_id", None):
        client_id = request.POST.get("client_id", None)
    elif request.POST.get("token", None):
        # introspect
        ac = AccessToken.objects.get(token=request.POST.get("token", None))

    try:

        if client_id is not None:
            app = Application.objects.get(client_id=client_id)
        elif ac is not None:
            app = Application.objects.get(id=ac.application_id)

        if app and not app.active:
            raise InvalidClientError(
                description=settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name)
            )

    except Application.DoesNotExist:
        pass

    if app and app.active:
        # Check for application RESEARCH_STUDY type end_date expired.
        if app.has_research_study_expired():
            raise InvalidClientError(
                description=settings.APPLICATION_RESEARCH_STUDY_ENDED_MESG
            )

        # Check for application ONE_TIME type where token refresh is not allowed.
        if app.has_one_time_only_data_access():
            # Is this for a token refresh?
            post_grant_type = request.POST.get("grant_type", None)
            if post_grant_type == "refresh_token":
                raise InvalidClientError(
                    description=settings.APPLICATION_ONE_TIME_REFRESH_NOT_ALLOWED_MESG
                )


def is_data_access_type_valid(data_access_type, end_date):
    """
    Validate data_access_type & end_date combo is valid.
        Returns: True/False & exception message for use.
    """
    if switch_is_active("limit_data_access"):
        if data_access_type == "RESEARCH_STUDY" and end_date is None:
            return False, "An end_date is required for the RESEARCH_STUDY type!"

        if data_access_type not in ["RESEARCH_STUDY", None] and end_date is not None:
            return False, "An end_date is ONLY required for the RESEARCH_STUDY type!"

    return True, None


def json_response_from_oauth2_errror(error):
    """
    Given a oauthlib.oauth2.rfc6749.errors.* error this function
    returns a corresponding django.http.response.JsonResponse response
    """
    ret_data = {"status_code": error.status_code, "error": error.error}

    # Add optional description
    if getattr(error, "description", None):
        ret_data["error_description"] = error.description

    return JsonResponse(ret_data, status=error.status_code)
