import datetime

from django.conf import settings
from django.shortcuts import render

from rest_framework import exceptions, status
from rest_framework.views import APIView

from apps.creds.utils import get_creds, get_url
from .models import ProdCredentialingReqest


class CredentialingRequestView(APIView):
    def get(self, request, *args, **kwargs):

        err = None
        creds_req_id = kwargs.get("prod_cred_req_id")
        fetch_action = request.query_params.get("action", "")

        if creds_req_id:

            creds_req = None

            try:
                creds_req = ProdCredentialingReqest.objects.get(creds_request_id=creds_req_id)
            except ProdCredentialingReqest.DoesNotExist:
                # log error
                pass

            if creds_req:
                creds_dict = get_creds(creds_req_id)
                # check if the generated creds request is expired
                if not self._is_expired(creds_req):
                    creds_req.visits_count = creds_req.visits_count + 1
                    creds_req.date_fetched = datetime.datetime.now(datetime.timezone.utc)
                    creds_req.last_visit = datetime.datetime.now(datetime.timezone.utc)
                    # fetch creds request and update visits count and relevant timestamps
                    creds_req.save()
                    ctx = {"fetch_creds_link": get_url(creds_req_id)}
                    ctx.update(creds_dict)
                    if fetch_action == "fetch":
                        ctx.update(fetch=True)
                    else:
                        # do not give out creds yet if not a fetch request
                        if "client_id" in ctx:
                            ctx.pop("client_id")
                        if "client_secret" in ctx:
                            ctx.pop("client_secret")
                    return render(request, 'get_creds.html', ctx)
                else:
                    err = exceptions.PermissionDenied("Generated credentialing request expired.", code=status.HTTP_403_FORBIDDEN)
            else:
                # not found
                err = exceptions.NotFound("Credentialing request not found.")
        else:
            # bad request
            err = exceptions.ValidationError("Credentialing request ID missing.", code=status.HTTP_400_BAD_REQUEST)

        raise err

    def _is_expired(self, creds_req):
        t_elapsed_since_created = datetime.datetime.now(datetime.timezone.utc) - creds_req.date_created
        return t_elapsed_since_created.seconds > settings.CREDENTIALS_REQUEST_URL_TTL * 60
