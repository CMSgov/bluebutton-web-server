import apps.logging.request_logger as logging
import datetime

from django.conf import settings
from django.http.response import JsonResponse
from django.shortcuts import render
from oauth2_provider.models import get_application_model
from rest_framework import exceptions, status
from rest_framework.views import APIView

from apps.creds.utils import get_app_usr_info, get_app_creds
from .models import CredentialingReqest

Application = get_application_model()


class CredentialingRequestView(APIView):
    def get(self, request, *args, **kwargs):
        logger = logging.getLogger(logging.AUDIT_CREDS_REQUEST_LOGGER, request)

        creds_req_id = kwargs.get("prod_cred_req_id")
        creds_req = self._get_creds_req(creds_req_id)
        action = request.query_params.get("action", "")

        self._validate_expiration(creds_req)

        log_dict = {
            "type": "credentials request",
            "id": creds_req_id,
        }

        response = None
        creds_dict = {}
        updated = False

        if action == "fetch" or action == "download":
            # generate new client_id, client_secret
            creds_dict = get_app_creds(creds_req_id)
            updated = True
            log_dict.update(
                {
                    "action": action,
                    "user_name": creds_dict["user_name"],
                    "org_name": creds_dict["org_name"],
                    "app_id": creds_dict["app_id"],
                    "app_name": creds_dict["app_name"],
                }
            )

        if action == "download":
            response = JsonResponse(creds_dict)
            response["Content-Disposition"] = 'attachment; filename="{}.json"'.format(
                creds_req_id
            )
        else:
            # response creds request page and update visits count and relevant timestamps
            app_usr_info = get_app_usr_info(creds_req)
            log_dict.update(app_usr_info)
            ctx = {"fetch": action}
            ctx.update(creds_dict)
            ctx.update(app_usr_info)
            response = render(request, "get_creds.html", ctx)

        self._update_creds_req_stats(creds_req, updated)

        logger.info(log_dict)

        return response

    def _validate_expiration(self, creds_req):
        t_elapsed_since_created = (
            datetime.datetime.now(datetime.timezone.utc) - creds_req.created_at
        )
        if t_elapsed_since_created.seconds > settings.CREDENTIALS_REQUEST_URL_TTL * 60:
            raise exceptions.PermissionDenied(
                "Generated credentialing request expired.",
                code=status.HTTP_403_FORBIDDEN,
            )

    def _get_creds_req(self, id):

        if not id:
            # bad request
            raise exceptions.ValidationError(
                "Credentialing request ID missing.", code=status.HTTP_400_BAD_REQUEST
            )

        creds_req = None

        try:
            creds_req = CredentialingReqest.objects.get(id=id)
        except CredentialingReqest.DoesNotExist:
            # not found
            raise exceptions.NotFound("Credentialing request not found.")

        return creds_req

    def _update_creds_req_stats(self, creds_req: CredentialingReqest, updated: False):
        creds_req.visits_count = creds_req.visits_count + 1
        creds_req.last_visit = datetime.datetime.now(datetime.timezone.utc)
        if updated:
            creds_req.updated_at = datetime.datetime.now(datetime.timezone.utc)
        creds_req.save()
