import logging
from oauth2_provider.signals import app_authorized
from django.db.models.signals import (
    post_delete,
)
from apps.fhir.bluebutton.views.generic import (
    pre_fetch,
    post_fetch
)
from .serializers import Token

audit = logging.getLogger('audit.%s' % __name__)


def handle_app_authorized(sender, request, token, **kwargs):
    audit.info(Token(token, action="authorized"))


def token_removed(sender, instance=None, **kwargs):
    audit.info(Token(instance, action="revoked"))


def fetching_data(sender, request=None, **kwargs):
    audit.info(request)


def fetched_data(sender, request=None, response=None, **kwargs):
    audit.info(request, response)


app_authorized.connect(handle_app_authorized)
post_delete.connect(token_removed, sender='oauth2_provider.AccessToken')
pre_fetch.connect(fetching_data)
post_fetch.connect(fetched_data)
