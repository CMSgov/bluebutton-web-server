import logging
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
    # Get auth flow uuid from session for logging
    auth_uuid = request.session.get('auth_uuid', None)

    token_logger.info(Token(token, action="authorized", auth_uuid=auth_uuid))


@receiver(beneficiary_authorized_application)
def handle_app_authorized(sender, request, user, application, **kwargs):
    # TODO: use json.dumps when rebasing with BB2-132
    token_logger.info({
        "type": "Authorization",
        "auth_uuid": request.session.get('auth_uuid', None),
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
    })


# BB2-218 also capture delete MyAccessToken
@receiver(post_delete, sender=MyAccessToken)
@receiver(post_delete, sender=AccessToken)
def token_removed(sender, instance=None, **kwargs):
    token_logger.info(Token(instance, action="revoked", auth_uuid=None))


@receiver(post_delete, sender=DataAccessGrant)
def log_grant_removed(sender, instance=None, **kwargs):
    token_logger.info(get_event(DataAccessGrantSerializer(instance, action="revoked")))


def fetching_data(sender, request=None, **kwargs):
    fhir_logger.info(get_event(FHIRRequest(request)))


def fetched_data(sender, request=None, response=None, **kwargs):
    fhir_logger.info(get_event(FHIRResponse(response)))


def sls_hook(sender, response=None, **kwargs):
    sls_logger.info(get_event(SLSResponse(response)))


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
