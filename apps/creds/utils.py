from django.conf import settings
from django.contrib.auth.models import User
from oauth2_provider.models import get_application_model

from apps.accounts.models import UserProfile

from .models import ProdCredentialingReqest


Application = get_application_model()


def get_url(creds_request_id):
    return "{}/creds/{}".format(settings.HOSTNAME_URL, creds_request_id)


def get_creds_by_id(creds_request_id: str):
    return get_creds_by_obj(ProdCredentialingReqest.objects.get(creds_request_id=creds_request_id))


def get_creds_by_obj(creds_req: ProdCredentialingReqest):
    creds_dict = {"user_name": None,
                  "org_name": None,
                  "app_name": None,
                  "client_id": None,
                  "client_secret": None}
    if creds_req:

        app = Application.objects.get(pk=creds_req.application_id)

        if app:
            creds_dict.update({
                "app_name": app.name,
                "client_id": app.client_id,
                "client_secret": app.client_secret, })

            user = User.objects.get(pk=app.user_id)

            if user:
                creds_dict.update({"user_name": user.username})
                usrprofile = UserProfile.objects.get(user=user)
                if usrprofile:
                    creds_dict.update({"org_name": usrprofile.organization_name})

    return creds_dict
