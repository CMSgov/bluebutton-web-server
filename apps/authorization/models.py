from datetime import datetime
from django.utils import timezone
from django.db import models
from django.db.models import Q
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
    token_count = (
        AccessToken.objects.filter(
            expires__gt=timezone.now(),
        )
        .values("user", "application")
        .distinct()
        .count()
    )
    grant_count = DataAccessGrant.objects.all().count()
    return {
        "unique_tokens": token_count,
        "grants": grant_count,
    }


def get_grant_bene_counts(application=None):
    """
    Get the grant counts for real/synth benes

    If application != None, the counts are for a specific application.
    """
    # Init counts dict
    counts_returned = {}

    # Grant real/synth bene counts (includes granted to multiple apps)
    start_time = datetime.utcnow().timestamp()

    # Setup base queryset
    grant_queryset = DataAccessGrant.objects

    if application:
        grant_queryset = grant_queryset.filter(application=application)

    real_grant_queryset = grant_queryset.filter(
        ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).values("beneficiary")

    synthetic_grant_queryset = grant_queryset.filter(
        Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).values("beneficiary")

    counts_returned["real"] = real_grant_queryset.count()
    counts_returned["synthetic"] = synthetic_grant_queryset.count()
    counts_returned["elapsed"] = round(datetime.utcnow().timestamp() - start_time, 3)

    # Grant real/synth bene distinct counts (excludes granted to multiple apps)
    if application is None:
        start_time = datetime.utcnow().timestamp()

        counts_returned["real_deduped"] = real_grant_queryset.distinct().count()
        counts_returned[
            "synthetic_deduped"
        ] = synthetic_grant_queryset.distinct().count()
        counts_returned["deduped_elapsed"] = round(
            datetime.utcnow().timestamp() - start_time, 3
        )

    # Archived grant real/synth bene distinct counts (excludes granted to multiple apps and multiple archived records)
    start_time = datetime.utcnow().timestamp()

    # Setup base queryset
    archived_queryset = ArchivedDataAccessGrant.objects

    if application:
        archived_queryset = archived_queryset.filter(application=application)

    real_archived_queryset = archived_queryset.filter(
        ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).values("beneficiary")

    synthetic_archived_queryset = archived_queryset.filter(
        Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).values("beneficiary")

    counts_returned["archived_real_deduped"] = real_archived_queryset.distinct().count()
    counts_returned[
        "archived_synthetic_deduped"
    ] = synthetic_archived_queryset.distinct().count()
    counts_returned["archived_deduped_elapsed"] = round(
        datetime.utcnow().timestamp() - start_time, 3
    )

    # Both Grant and Archived grant (UNION) real/synth bene distinct counts
    start_time = datetime.utcnow().timestamp()

    real_union_queryset = real_grant_queryset.union(real_archived_queryset)
    synthetic_union_queryset = synthetic_grant_queryset.union(
        synthetic_archived_queryset
    )

    counts_returned[
        "grant_and_archived_real_deduped"
    ] = real_union_queryset.distinct().count()
    counts_returned[
        "grant_and_archived_synthetic_deduped"
    ] = synthetic_union_queryset.count()
    counts_returned["grant_and_archived_deduped_elapsed"] = round(
        datetime.utcnow().timestamp() - start_time, 3
    )

    return counts_returned
