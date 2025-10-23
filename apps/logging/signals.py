import apps.logging.request_logger as logging

from django.db.models.signals import (
    post_delete,
)
from django.dispatch import receiver
from oauth2_provider.models import AccessToken
from oauth2_provider.signals import app_authorized

from apps.authorization.models import DataAccessGrant
from apps.dot_ext.admin import MyAccessToken
from apps.dot_ext.signals import beneficiary_authorized_application
from apps.fhir.bluebutton.signals import (
    pre_fetch,
    post_fetch
)

from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.utils import FhirServerAuth
from apps.mymedicare_cb.signals import post_sls

from .serializers import (
    Token,
    DataAccessGrantSerializer,
    FHIRRequest,
    FHIRRequestForAuth,
    FHIRResponse,
    FHIRResponseForAuth,
)


@receiver(app_authorized)
def handle_token_created(sender, request, token, **kwargs):
    # Get auth flow dict from session for logging
    token_logger = logging.getLogger(logging.AUDIT_AUTHZ_TOKEN_LOGGER, request)
    token_logger.info(Token(token, action="authorized").to_dict())


@receiver(beneficiary_authorized_application)
def handle_app_authorized(sender, request, auth_status, auth_status_code, user, application,
                          share_demographic_scopes, scopes, allow, access_token_delete_cnt,
                          refresh_token_delete_cnt, data_access_grant_delete_cnt, **kwargs):

    token_logger = logging.getLogger(logging.AUDIT_AUTHZ_TOKEN_LOGGER, request)
    crosswalk_log = {
        'id': None,
        'user_hicn_hash': None,
        'user_mbi': None,
        # BB2-4166-TODO: this is hardcoded to be version 2, add v3
        'fhir_id_v2': None,
        'user_id_type': None
    }

    try:
        crosswalk_log = {
            'id': user.crosswalk.id,
            'user_hicn_hash': user.crosswalk.user_hicn_hash,
            'user_mbi': user.crosswalk.user_mbi,
            # BB2-4166-TODO: this is hardcoded to be version 2, add v3
            'fhir_id_v2': user.crosswalk.fhir_id(2),
            'user_id_type': user.crosswalk.user_id_type
        }
    except Exception:
        # TODO consider logging exception name here
        # once we get the generic logger hooked up
        pass

    log_dict = {
        'type': 'Authorization',
        'auth_status': auth_status,
        'auth_status_code': auth_status_code,
        'user': {
            'id': user.id,
            'username': user.username,
            'crosswalk': crosswalk_log,
        },
        'application': {
            'id': application.id,
            'name': application.name,
            'data_access_type': application.data_access_type,
        },
        'share_demographic_scopes': share_demographic_scopes,
        'scopes': scopes,
        'allow': allow,
        'access_token_delete_cnt': access_token_delete_cnt,
        'refresh_token_delete_cnt': access_token_delete_cnt,
        'data_access_grant_delete_cnt': data_access_grant_delete_cnt,
    }

    token_logger.info(log_dict)


# BB2-218 also capture delete MyAccessToken
@receiver(post_delete, sender=MyAccessToken)
@receiver(post_delete, sender=AccessToken)
def token_removed(sender, instance=None, **kwargs):
    token_logger = logging.getLogger(logging.AUDIT_AUTHZ_TOKEN_LOGGER)
    token_logger.info(Token(instance, action="revoked").to_dict())


@receiver(post_delete, sender=DataAccessGrant)
def log_grant_removed(sender, instance=None, **kwargs):
    token_logger = logging.getLogger(logging.AUDIT_AUTHZ_TOKEN_LOGGER)
    token_logger.info(DataAccessGrantSerializer(instance, action="revoked").to_dict())


@receiver(pre_fetch, sender=FhirDataView)
@receiver(pre_fetch, sender=FhirServerAuth)
def fetching_data(sender, request=None, auth_request=None, api_ver=None, **kwargs):
    fhir_logger = logging.getLogger(logging.AUDIT_DATA_FHIR_LOGGER, auth_request)
    fhir_logger.info(FHIRRequest(request, api_ver).to_dict()
                     if sender == FhirDataView
                     else FHIRRequestForAuth(request, api_ver).to_dict())


@receiver(post_fetch, sender=FhirDataView)
@receiver(post_fetch, sender=FhirServerAuth)
def fetched_data(sender, request=None, auth_request=None, response=None, api_ver=None, **kwargs):
    fhir_logger = logging.getLogger(logging.AUDIT_DATA_FHIR_LOGGER, auth_request)
    fhir_logger.info(FHIRResponse(response, api_ver).to_dict()
                     if sender == FhirDataView
                     else FHIRResponseForAuth(response, api_ver).to_dict())


def sls_hook(sender, response=None, request=None, **kwargs):
    # Handles sender for SLSxUserInfoResponse, or SLSxTokenResponse
    # here request - callback request
    sls_logger = logging.getLogger(logging.AUDIT_AUTHZ_SLS_LOGGER, request)
    sls_logger.info(sender(response).to_dict())


post_sls.connect(sls_hook)
