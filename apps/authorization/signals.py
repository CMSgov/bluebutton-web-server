from oauth2_provider.signals import app_authorized
from .models import DataAccessGrant


def app_authorized_record_grant(sender, request, token, **kwargs):
    DataAccessGrant.objects.get_or_create(
        beneficiary = token.user,
        application = token.application,
    )


app_authorized.connect(app_authorized_record_grant)
