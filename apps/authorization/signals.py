from oauth2_provider.signals import app_authorized
from oauth2_provider.models import get_access_token_model
from django.db.models.signals import (
    post_delete,
)
from .models import DataAccessGrant

AccessToken = get_access_token_model()


class DataAccessGrantSerializer:
    tkn = None
    action = None

    def __init__(self, obj, action=None):
        self.tkn = obj
        self.action = action

    def __str__(self):
        # seems like this should be a serializer
        result = {
            "type": "AccessToken",
            "action": self.action,
            "id": self.tkn.pk,
            "application": {
                "id": self.tkn.application.id,
                "name": self.tkn.application.name,
                "user": {
                    "id": self.tkn.application.user.id,
                    "username": self.tkn.application.user.username,
                },
            },
            "user": {
                "id": self.tkn.user.id,
                "username": self.tkn.user.username,
            }
        }
        return json.dumps(result)

def app_authorized_record_grant(sender, request, token, **kwargs):
    DataAccessGrant.objects.get_or_create(
        beneficiary=token.user,
        application=token.application,
    )


app_authorized.connect(app_authorized_record_grant)

def revoke_associated_tokens(sender, instance=None, **kwargs):
    tokens = AccessToken.objects.filter(application=instance.application, user=instance.user).all()
    for token in tokens:
        token.revoke()

def log_grant_removed(sender, instance=None, **kwargs):
    token_logger.info(DataAccessGrantSerializer(instance, action="revoked"))


post_delete.connect(remove_associated_tokens, sender='apps.authorization.DataAccessGrant')
post_delete.connect(log_grant_removed, sender='apps.authorization.DataAccessGrant')
