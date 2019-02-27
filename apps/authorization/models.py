from django.utils import timezone
from django.db import models
from django.conf import settings
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.models import get_access_token_model


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
