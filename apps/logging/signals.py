import logging
from oauth2_provider.signals import app_authorized
from django.db.models.signals import (
    post_delete,
)
from .serializers import Token

audit = logging.getLogger('audit.%s' % __name__)


def handle_app_authorized(sender, request, token, **kwargs):
    audit.info(Token(token, action="authorized"))


def token_removed(sender, instance=None, **kwargs):
    audit.info(Token(instance, action="revoked"))


app_authorized.connect(handle_app_authorized)
post_delete.connect(token_removed, sender='oauth2_provider.AccessToken')
