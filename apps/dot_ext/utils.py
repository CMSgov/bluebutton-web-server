from django.db import transaction
from oauth2_provider.models import AccessToken, RefreshToken
from apps.authorization.models import DataAccessGrant
from oauth2_provider.models import get_application_model
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.conf import settings

Application = get_application_model()
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
        access_token_delete_cnt = AccessToken.objects.filter(application=application, user=user).count()

        # Delete DataAccessGrant record.
        # NOTE: This also revokes/deletes access and only revokes refresh tokens via signal function.
        data_access_grant_delete_cnt = DataAccessGrant.objects.filter(application=application, beneficiary=user).delete()[0]

        # Delete refresh token records
        refresh_token_delete_cnt = RefreshToken.objects.filter(application=application, user=user).delete()[0]

    return data_access_grant_delete_cnt, access_token_delete_cnt, refresh_token_delete_cnt


def validate_app_is_active(request):

    client_id, ac, app = None, None, None

    if request.GET.get('client_id', None) is not None:
        client_id = request.GET.get('client_id', None)
    elif request.POST.get('client_id', None):
        client_id = request.POST.get('client_id', None)
    elif request.POST.get('token', None):
        # introspect
        ac = AccessToken.objects.get(token=request.POST.get('token', None))

    try:

        if client_id is not None:
            app = Application.objects.get(client_id=client_id)
        elif ac is not None:
            app = Application.objects.get(id=ac.application_id)

        if app and not app.active:
            raise PermissionDenied(settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name))

    except Application.DoesNotExist:
        pass
