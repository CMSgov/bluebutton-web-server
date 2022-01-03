import apps.logging.request_logger as logging
import datetime

from django.conf import settings
from django.http.response import JsonResponse
from django.shortcuts import render
from oauth2_provider.models import get_application_model
from rest_framework import exceptions, status
from rest_framework.views import APIView

from apps.creds.utils import get_creds_by_obj, get_url
from .models import CredentialingReqest

Application = get_application_model()


class CredentialingRequestView(APIView):
    def get(self, request, *args, **kwargs):
        logger = logging.getLogger(logging.AUDIT_CREDS_REQUEST_LOGGER, request)

        creds_req_id = kwargs.get("prod_cred_req_id")

        creds_req = self._get_creds_req(creds_req_id)

        # check if expired
        if self._is_expired(creds_req):
            raise exceptions.PermissionDenied("Generated credentialing request expired.", code=status.HTTP_403_FORBIDDEN)

        creds_dict = get_creds_by_obj(creds_req)
        # fetch creds request and update visits count and relevant timestamps
        creds_req.visits_count = creds_req.visits_count + 1
        creds_req.last_visit = datetime.datetime.now(datetime.timezone.utc)

        ctx = {"fetch_creds_link": get_url(creds_req_id)}
        ctx.update(creds_dict)

        log_dict = {
            "type": "credentials request",
            "id": creds_req_id,
            "app_id": ctx.get("app_id", ""),
            "app_name": ctx.get("app_name", ""),
        }

        action = request.query_params.get("action", "")

        if action == "fetch" or action == "download":
            if creds_req.updated_at is None:
                creds_req.updated_at = datetime.datetime.now(datetime.timezone.utc)
                ctx.update(fetch=action)
                log_dict.update(action=action)
            else:
                # already fetched, fetch again forbidden
                raise exceptions.PermissionDenied("Credentials already fetched (download), doing it again not allowed.",
                                                  code=status.HTTP_403_FORBIDDEN)
        else:
            # do not give out creds yet if not a fetch request
            if "client_id" in ctx:
                ctx.pop("client_id")
            if "client_secret" in ctx:
                ctx.pop("client_secret")
        # update visits and fetch status etc.
        creds_req.save()

        logger.info(log_dict)

        if action == "download":
            response = JsonResponse(creds_dict)
            response['Content-Disposition'] = 'attachment; filename="{}.json"'.format(creds_req_id)
            return response
        else:
            return render(request, 'get_creds.html', ctx)

    def _is_expired(self, creds_req):
        t_elapsed_since_created = datetime.datetime.now(datetime.timezone.utc) - creds_req.created_at
        return t_elapsed_since_created.seconds > settings.CREDENTIALS_REQUEST_URL_TTL * 60

    def _get_creds_req(self, id):

        if not id:
            # bad request
            raise exceptions.ValidationError("Credentialing request ID missing.", code=status.HTTP_400_BAD_REQUEST)

        creds_req = None

        try:
            creds_req = CredentialingReqest.objects.get(id=id)
        except CredentialingReqest.DoesNotExist:
            # not found
            raise exceptions.NotFound("Credentialing request not found.")

        return creds_req
