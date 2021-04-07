from django.utils import timezone
from django.db import models
from django.db.models import Q
from django.conf import settings
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.models import get_access_token_model, get_application_model


class DataAccessGrant(models.Model):
    beneficiary = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    application = models.ForeignKey(
        oauth2_settings.APPLICATION_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("beneficiary", "application")
        indexes = [
            models.Index(fields=["beneficiary", "application"]),
            models.Index(fields=["beneficiary"]),
            models.Index(fields=["application"]),
        ]

    @property
    def user(self):
        return self.beneficiary


class ArchivedDataAccessGrant(models.Model):
    beneficiary = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_constraint=False,
        null=True,
    )
    application = models.ForeignKey(
        oauth2_settings.APPLICATION_MODEL,
        on_delete=models.CASCADE,
        db_constraint=False,
        null=True,
    )
    created_at = models.DateTimeField()
    archived_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["beneficiary"]),
            models.Index(fields=["application"]),
        ]

    @property
    def user(self):
        return self.beneficiary


def update_grants(*args, **kwargs):
    AccessToken = get_access_token_model()
    # inefficient version
    tokens = AccessToken.objects.all()
    for token in tokens:
        if token.is_valid():
            DataAccessGrant.objects.get_or_create(
                beneficiary=token.user,
                application=token.application,
            )


def check_grants():
    AccessToken = get_access_token_model()
    token_count = AccessToken.objects.filter(
        expires__gt=timezone.now(),
    ).values('user', 'application').distinct().count()
    grant_count = DataAccessGrant.objects.all().count()
    return {
        "unique_tokens": token_count,
        "grants": grant_count,
    }


def get_application_bene_grant_counts(app_id=None):
    '''
    Get the real and synthetic counts of beneficiaries from DataAccessGrant for an application.
    '''
    Application = get_application_model()

    try:
        app = Application.objects.get(id=app_id)
        if app is not None:
            grant_user_real_count = DataAccessGrant.objects.filter(
                application=app).values('application', 'beneficiary').distinct().filter(
                    ~Q(beneficiary__crosswalk___fhir_id__startswith='-')
                    & ~Q(beneficiary__crosswalk___fhir_id='')).count()

            grant_user_synth_count = DataAccessGrant.objects.filter(
                application=app).values('application', 'beneficiary').distinct().filter(
                    Q(beneficiary__crosswalk___fhir_id__startswith='-')).count()
        return {
            "real": grant_user_real_count,
            "synthetic": grant_user_synth_count,
        }
    except ValueError:
        pass
    except Application.DoesNotExist:
        pass

    return {
        "synthetic": None,
        "real": None,
    }
