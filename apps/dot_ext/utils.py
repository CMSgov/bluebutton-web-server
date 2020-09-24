from django.db import transaction
from oauth2_provider.models import AccessToken, RefreshToken


def remove_application_user_pair_tokens(application, user):
    """
    Utility function to remove current application/user pair
    access_token and refresh_token records.

    This is to be used related to changes in a choice for a beneficiary
    to not share or an application to not require demographic scopes.

    This ensures that previously created tokens, with full scopes, can not
    be used when there is a change.

    RETURN:
        access_token_delete_cnt = Access tokens deleted.
        refresh_token_delete_cnt = Refresh tokens deleted.

    CALLED FROM:
        apps.dot_ext.views.authorization.authorization.AuthorizationView.form_valid()
    """
    with transaction.atomic():
        access_token_delete_cnt = AccessToken.objects.filter(application=application, user=user).delete()[0]
        refresh_token_delete_cnt = RefreshToken.objects.filter(application=application, user=user).delete()[0]

    return access_token_delete_cnt, refresh_token_delete_cnt
