from oauth2_provider.signals import app_authorized
from oauth2_provider.models import get_access_token_model
from django.db.models.signals import (
    post_delete,
)
from .models import DataAccessGrant, ArchivedDataAccessGrant

AccessToken = get_access_token_model()


def app_authorized_record_grant(sender, request, token, application=None, **kwargs):
    bene = request.user
    if token is not None:
        bene = token.user
        application = token.application

    DataAccessGrant.objects.get_or_create(
        beneficiary=bene,
        application=application,
    )


app_authorized.connect(app_authorized_record_grant)


def revoke_associated_tokens(sender, instance=None, **kwargs):
    tokens = AccessToken.objects.filter(application=instance.application, user=instance.user).all()
    for token in tokens:
        token.revoke()


def archive_removed_grant(sender, instance=None, **kwargs):
    ArchivedDataAccessGrant.objects.create(
        created_at=instance.created_at,
        application=instance.application,
        beneficiary=instance.beneficiary)


post_delete.connect(revoke_associated_tokens, sender='authorization.DataAccessGrant')
post_delete.connect(archive_removed_grant, sender='authorization.DataAccessGrant')
