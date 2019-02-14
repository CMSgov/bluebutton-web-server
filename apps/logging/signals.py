import logging
from oauth2_provider.signals import app_authorized
from django.db.models.signals import (
    post_delete,
)
from apps.fhir.bluebutton.signals import (
    pre_fetch,
    post_fetch
)
from apps.mymedicare_cb.signals import post_sls

from .serializers import (
    Token,
    DataAccessGrantSerializer,
    FHIRRequest,
    FHIRResponse,
    SLSResponse,
)

token_logger = logging.getLogger('audit.authorization.token')
sls_logger = logging.getLogger('audit.authorization.sls')
fhir_logger = logging.getLogger('audit.data.fhir')


def handle_app_authorized(sender, request, token, **kwargs):
    token_logger.info(Token(token, action="authorized"))


def token_removed(sender, instance=None, **kwargs):
    token_logger.info(Token(instance, action="revoked"))


def log_grant_removed(sender, instance=None, **kwargs):
    token_logger.info(DataAccessGrantSerializer(instance, action="revoked"))


def fetching_data(sender, request=None, **kwargs):
    fhir_logger.info(FHIRRequest(request))


def fetched_data(sender, request=None, response=None, **kwargs):
    fhir_logger.info(FHIRResponse(response))


def sls_hook(sender, response=None, **kwargs):
    sls_logger.info(SLSResponse(response))


app_authorized.connect(handle_app_authorized)
post_delete.connect(token_removed, sender='oauth2_provider.AccessToken')
post_delete.connect(log_grant_removed, sender='authorization.DataAccessGrant')
pre_fetch.connect(fetching_data)
post_fetch.connect(fetched_data)
post_sls.connect(sls_hook)
