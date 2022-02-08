import string

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.utils import IntegrityError
from oauth2_provider.models import get_application_model
from oauth2_provider.generators import generate_client_id, generate_client_secret
from rest_framework import exceptions, status

from apps.accounts.models import UserProfile

from .models import CredentialingReqest


Application = get_application_model()


def get_url(creds_request_id):
    return "{}/creds/{}".format(settings.HOSTNAME_URL, creds_request_id)


def get_new_creds(creds_request_id: string):

    creds_dict = {
        "user_name": None,
        "org_name": None,
        "app_id": None,
        "app_name": None,
        "client_id": None,
        "client_secret": None,
        "creds_req_id": creds_request_id,
    }

    creds_req = CredentialingReqest.objects.get(id=creds_request_id)

    creds_dict = get_app_usr_info(creds_req)

    if creds_req.updated_at is not None:
        raise exceptions.PermissionDenied(
            "Credentials already fetched (download), doing it again not allowed.",
            code=status.HTTP_403_FORBIDDEN,
        )

    app = Application.objects.get(pk=creds_req.application_id)

    try:
        with transaction.atomic():

            if app:

                client_id = generate_client_id()
                client_secret = generate_client_secret()

                app.client_id = client_id
                app.client_secret = client_secret
                app.save()

                creds_dict.update(
                    {
                        "client_id": client_id,
                        "client_secret": client_secret,
                    }
                )
    except IntegrityError:
        pass

    return creds_dict


def get_app_usr_info(creds_req: CredentialingReqest):

    app_usr_info = {
        "user_name": None,
        "org_name": None,
        "app_id": None,
        "app_name": None,
        "creds_req_id": creds_req.id,
    }

    app = Application.objects.get(pk=creds_req.application_id)

    if app:
        app_usr_info.update(
            {
                "app_id": app.id,
                "app_name": app.name,
            }
        )

        user = User.objects.get(pk=app.user_id)

        if user:
            app_usr_info.update({"user_name": user.username})
            usrprofile = UserProfile.objects.get(user=user)
            if usrprofile:
                app_usr_info.update({"org_name": usrprofile.organization_name})

    return app_usr_info
