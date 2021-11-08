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


def get_grant_counts():
    # Grant real/synth bene counts (includes granted to multiple apps)
    start_time = datetime.utcnow().timestamp()

    real_bene_cnt = DataAccessGrant.objects.filter(
        ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).count()

    synth_bene_cnt = DataAccessGrant.objects.filter(
        Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).count()

    bene_cnt_elapsed = round(datetime.utcnow().timestamp() - start_time, 3)

    # Grant real/synth bene distinct counts (excludes granted to multiple apps)
    start_time = datetime.utcnow().timestamp()

    real_bene_distinct_cnt = (
        DataAccessGrant.objects.order_by("beneficiary__username")
        .filter(
            ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .values("beneficiary__username")
        .distinct()
        .count()
    )

    synth_bene_distinct_cnt = (
        DataAccessGrant.objects.order_by("beneficiary__username")
        .filter(
            Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .values("beneficiary__username")
        .distinct()
        .count()
    )

    bene_distinct_cnt_elapsed = round(datetime.utcnow().timestamp() - start_time, 3)

    # Archived grant real/synth bene distinct counts (excludes granted to multiple apps and multiple archived records)
    start_time = datetime.utcnow().timestamp()

    real_bene_arch_distinct_cnt = (
        ArchivedDataAccessGrant.objects.filter(
            ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .distinct()
        .count()
    )

    synth_bene_arch_distinct_cnt = (
        ArchivedDataAccessGrant.objects.filter(
            Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .distinct()
        .count()
    )

    bene_arch_distinct_cnt_elapsed = round(
        datetime.utcnow().timestamp() - start_time, 3
    )

    # Both Grant and Archived grant (UNION) real/synth bene distinct counts
    start_time = datetime.utcnow().timestamp()

    real_bene_union_cnt = (
        DataAccessGrant.objects.filter(
            ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .values("beneficiary__username")
        .union(
            ArchivedDataAccessGrant.objects.filter(
                ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
                & ~Q(beneficiary__crosswalk___fhir_id="")
                & Q(beneficiary__crosswalk___fhir_id__isnull=False)
            ).values("beneficiary__username")
        )
        .count()
    )

    synth_bene_union_cnt = (
        DataAccessGrant.objects.filter(
            Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .values("beneficiary__username")
        .union(
            ArchivedDataAccessGrant.objects.filter(
                Q(beneficiary__crosswalk___fhir_id__startswith="-")
                & ~Q(beneficiary__crosswalk___fhir_id="")
                & Q(beneficiary__crosswalk___fhir_id__isnull=False)
            ).values("beneficiary__username")
        )
        .count()
    )

    bene_union_cnt_elapsed = round(datetime.utcnow().timestamp() - start_time, 3)

    return {
        "real_bene_cnt": real_bene_cnt,
        "synth_bene_cnt": synth_bene_cnt,
        "bene_cnt_elapsed": bene_cnt_elapsed,
        "real_bene_distinct_cnt": real_bene_distinct_cnt,
        "synth_bene_distinct_cnt": synth_bene_distinct_cnt,
        "bene_distinct_cnt_elapsed": bene_distinct_cnt_elapsed,
        "real_bene_arch_distinct_cnt": real_bene_arch_distinct_cnt,
        "synth_bene_arch_distinct_cnt": synth_bene_arch_distinct_cnt,
        "bene_arch_distinct_cnt_elapsed": bene_arch_distinct_cnt_elapsed,
        "real_bene_union_cnt": real_bene_union_cnt,
        "synth_bene_union_cnt": synth_bene_union_cnt,
        "bene_union_cnt_elapsed": bene_union_cnt_elapsed,
    }


def get_grant_by_app_counts(application):
    """
    Get grant related counts for a single application
    """

    # Grant real/synth bene counts
    real_bene_cnt = DataAccessGrant.objects.filter(
        Q(application=application)
        & ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).count()

    synth_bene_cnt = DataAccessGrant.objects.filter(
        Q(application=application)
        & Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).count()

    # Archived grant real/synth bene distinct counts
    real_bene_arch_distinct_cnt = (
        ArchivedDataAccessGrant.objects.filter(
            Q(application=application)
            & ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .distinct()
        .count()
    )
    synth_bene_arch_distinct_cnt = (
        ArchivedDataAccessGrant.objects.filter(
            Q(application=application)
            & Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .distinct()
        .count()
    )

    # Both Grant and Archived grant (UNION) real/synth bene distinct counts
    real_bene_union_cnt = (
        DataAccessGrant.objects.filter(
            Q(application=application)
            & ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .values("beneficiary__username")
        .union(
            ArchivedDataAccessGrant.objects.filter(
                Q(application=application)
                & ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
                & ~Q(beneficiary__crosswalk___fhir_id="")
                & Q(beneficiary__crosswalk___fhir_id__isnull=False)
            ).values("beneficiary__username")
        )
        .count()
    )
    synth_bene_union_cnt = (
        DataAccessGrant.objects.filter(
            Q(application=application)
            & Q(beneficiary__crosswalk___fhir_id__startswith="-")
            & ~Q(beneficiary__crosswalk___fhir_id="")
            & Q(beneficiary__crosswalk___fhir_id__isnull=False)
        )
        .values("beneficiary__username")
        .union(
            ArchivedDataAccessGrant.objects.filter(
                Q(application=application)
                & Q(beneficiary__crosswalk___fhir_id__startswith="-")
                & ~Q(beneficiary__crosswalk___fhir_id="")
                & Q(beneficiary__crosswalk___fhir_id__isnull=False)
            ).values("beneficiary__username")
        )
        .count()
    )

    return {
        "real_bene_cnt": real_bene_cnt,
        "synth_bene_cnt": synth_bene_cnt,
        "real_bene_arch_distinct_cnt": real_bene_arch_distinct_cnt,
        "synth_bene_arch_distinct_cnt": synth_bene_arch_distinct_cnt,
        "real_bene_union_cnt": real_bene_union_cnt,
        "synth_bene_union_cnt": synth_bene_union_cnt,
    }
