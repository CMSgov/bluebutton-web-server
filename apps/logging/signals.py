import json
import logging
import sys
import traceback
from django.db.models.signals import (
    post_delete,
)
from django.dispatch import receiver
from oauth2_provider.models import AccessToken
from oauth2_provider.signals import app_authorized

from apps.authorization.models import DataAccessGrant
from apps.dot_ext.admin import MyAccessToken
from apps.dot_ext.loggers import get_session_auth_flow_trace
from apps.dot_ext.signals import beneficiary_authorized_application
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


@receiver(app_authorized)
def handle_token_created(sender, request, token, **kwargs):
    # Get auth flow dict from session for logging
    auth_flow_dict = get_session_auth_flow_trace(request)

    token_logger.info(get_event(Token(token, action="authorized", auth_flow_dict=auth_flow_dict)))


@receiver(beneficiary_authorized_application)
def handle_app_authorized(sender, request, auth_status, auth_status_code, user, application,
                          share_demographic_scopes, scopes, allow, **kwargs):

    # Get auth flow dict from session for logging
    auth_flow_dict = get_session_auth_flow_trace(request)

    token_logger.info(get_event(json.dumps({
        "type": "Authorization",
        "auth_uuid": auth_flow_dict.get('auth_uuid', None),
        "auth_app_id": auth_flow_dict.get('auth_app_id', None),
        "auth_app_name": auth_flow_dict.get('auth_app_name', None),
        "auth_client_id": auth_flow_dict.get('auth_client_id', None),
        "auth_pkce_method": auth_flow_dict.get('auth_pkce_method', None),
        "auth_status": auth_status,
        "auth_status_code": auth_status_code,
        "user": {
            "id": user.id,
            "username": user.username,
            "crosswalk": {
                "id": user.crosswalk.id,
                "user_hicn_hash": user.crosswalk.user_hicn_hash,
                "user_mbi_hash": user.crosswalk.user_mbi_hash,
                "fhir_id": user.crosswalk.fhir_id,
                "user_id_type": user.crosswalk.user_id_type,
            },
        },
        "application": {
            "id": application.id,
            "name": application.name,
        },
        "share_demographic_scopes": share_demographic_scopes,
        "scopes": scopes,
        "allow": allow,
    })))


# BB2-218 also capture delete MyAccessToken
@receiver(post_delete, sender=MyAccessToken)
@receiver(post_delete, sender=AccessToken)
def token_removed(sender, instance=None, **kwargs):
    token_logger.info(get_event(Token(instance, action="revoked", auth_flow_dict=None)))


@receiver(post_delete, sender=DataAccessGrant)
def log_grant_removed(sender, instance=None, **kwargs):
    token_logger.info(get_event(DataAccessGrantSerializer(instance, action="revoked")))


def fetching_data(sender, request=None, **kwargs):
    fhir_logger.info(get_event(FHIRRequest(request)))


def fetched_data(sender, request=None, response=None, **kwargs):
    fhir_logger.info(get_event(FHIRResponse(response)))


def sls_hook(sender, response=None, auth_uuid=None, **kwargs):
    sls_logger.info(get_event(sender(response, auth_uuid)))


def get_event(event):
    '''
    helper to evaluate event and supress any error
    '''
    event_str = None
    try:
        event_str = str(event)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        event_str = traceback.format_exception(exc_type, exc_value, exc_traceback)
    return event_str


pre_fetch.connect(fetching_data)
post_fetch.connect(fetched_data)
post_sls.connect(sls_hook)
