from datetime import datetime
from django.db import models
from django.db.models import Count, Min, Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

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

    # Get total table count
    counts_returned["total"] = grant_queryset.count()

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

    # Get total table count
    counts_returned["archived_total"] = archived_queryset.count()

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

    # Django 3.2.13 upgrade: seems need to re-write the query to work around?
    # django.db.utils.NotSupportedError: Calling QuerySet.distinct() after union() is not supported
    # and below is the quote from Django doc:
    #
    # union()
    # union(*other_qs, all=False)
    # Uses SQL’s UNION operator to combine the results of two or more QuerySets. For example:
    #
    # >>> qs1.union(qs2, qs3)
    # The UNION operator selects only distinct values by default. To allow duplicate values, use the all=True argument.

    # counts_returned[
    #     "grant_and_archived_real_deduped"
    # ] = real_union_queryset.distinct().count()
    counts_returned[
        "grant_and_archived_real_deduped"
    ] = real_union_queryset.count()
    counts_returned[
        "grant_and_archived_synthetic_deduped"
    ] = synthetic_union_queryset.count()
    counts_returned["grant_and_archived_deduped_elapsed"] = round(
        datetime.utcnow().timestamp() - start_time, 3
    )

    return counts_returned


def get_beneficiary_counts():
    """
    Get AccessToken, DataAccessGrant
    and ArchivedDataAccessGrant counts for beneficiary type users.
    """
    User = get_user_model()

    # Init counts dict
    counts_returned = {}

    start_time = datetime.utcnow().timestamp()

    queryset = (
        User.objects.select_related()
        .filter(userprofile__user_type="BEN")
        .annotate(
            fhir_id=Min("crosswalk___fhir_id"),
            grant_count=Count("dataaccessgrant__application", distinct=True),
            grant_archived_count=Count(
                "archiveddataaccessgrant__application", distinct=True
            ),
        )
        .all()
    )

    # Count should be equal to Crosswalk
    counts_returned["total"] = queryset.count()

    # Setup base Real queryset
    real_queryset = queryset.filter(~Q(fhir_id__startswith="-") & ~Q(fhir_id=""))

    # Setup base synthetic queryset
    synthetic_queryset = queryset.filter(Q(fhir_id__startswith="-") & ~Q(fhir_id=""))

    # Real/synth counts. This should match counts using the Crosswalk table directly.
    counts_returned["real"] = real_queryset.count()
    counts_returned["synthetic"] = synthetic_queryset.count()

    """
    Grant related count section
    """
    # Count only if in grant
    counts_returned["total_grant"] = queryset.filter(Q(grant_count__gt=0)).count()
    counts_returned["real_grant"] = real_queryset.filter(Q(grant_count__gt=0)).count()
    counts_returned["synthetic_grant"] = synthetic_queryset.filter(
        Q(grant_count__gt=0)
    ).count()

    # Count only if in grant archived
    counts_returned["total_grant_archived"] = queryset.filter(
        Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["real_grant_archived"] = real_queryset.filter(
        Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["synthetic_grant_archived"] = synthetic_queryset.filter(
        Q(grant_archived_count__gt=0)
    ).count()

    # Count only if in grant OR archived
    counts_returned["total_grant_or_archived"] = queryset.filter(
        Q(grant_count__gt=0) | Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["real_grant_or_archived"] = real_queryset.filter(
        Q(grant_count__gt=0) | Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["synthetic_grant_or_archived"] = synthetic_queryset.filter(
        Q(grant_count__gt=0) | Q(grant_archived_count__gt=0)
    ).count()

    # Count only if in grant AND archived
    counts_returned["total_grant_and_archived"] = queryset.filter(
        Q(grant_count__gt=0) & Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["real_grant_and_archived"] = real_queryset.filter(
        Q(grant_count__gt=0) & Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["synthetic_grant_and_archived"] = synthetic_queryset.filter(
        Q(grant_count__gt=0) & Q(grant_archived_count__gt=0)
    ).count()

    # Count only if in grant NOT archived
    counts_returned["total_grant_not_archived"] = queryset.filter(
        Q(grant_count__gt=0) & ~Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["real_grant_not_archived"] = real_queryset.filter(
        Q(grant_count__gt=0) & ~Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["synthetic_grant_not_archived"] = synthetic_queryset.filter(
        Q(grant_count__gt=0) & ~Q(grant_archived_count__gt=0)
    ).count()

    # Count only if in archived NOT grant
    counts_returned["total_archived_not_grant"] = queryset.filter(
        ~Q(grant_count__gt=0) & Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["real_archived_not_grant"] = real_queryset.filter(
        ~Q(grant_count__gt=0) & Q(grant_archived_count__gt=0)
    ).count()
    counts_returned["synthetic_archived_not_grant"] = synthetic_queryset.filter(
        ~Q(grant_count__gt=0) & Q(grant_archived_count__gt=0)
    ).count()

    """
    Bene grants to applications break down count section
    """
    counts_returned["real_grant_to_apps_eq_1"] = real_queryset.filter(
        Q(grant_count=1)
    ).count()
    counts_returned["synthetic_grant_to_apps_eq_1"] = synthetic_queryset.filter(
        Q(grant_count=1)
    ).count()

    counts_returned["real_grant_to_apps_eq_2"] = real_queryset.filter(
        Q(grant_count=2)
    ).count()
    counts_returned["synthetic_grant_to_apps_eq_2"] = synthetic_queryset.filter(
        Q(grant_count=2)
    ).count()

    counts_returned["real_grant_to_apps_eq_3"] = real_queryset.filter(
        Q(grant_count=3)
    ).count()
    counts_returned["synthetic_grant_to_apps_eq_3"] = synthetic_queryset.filter(
        Q(grant_count=3)
    ).count()

    counts_returned["real_grant_to_apps_eq_4thru5"] = real_queryset.filter(
        Q(grant_count__gte=4) & Q(grant_count__lte=5)
    ).count()
    counts_returned["synthetic_grant_to_apps_eq_4thru5"] = synthetic_queryset.filter(
        Q(grant_count__gte=4) & Q(grant_count__lte=5)
    ).count()

    counts_returned["real_grant_to_apps_eq_6thru8"] = real_queryset.filter(
        Q(grant_count__gte=6) & Q(grant_count__lte=8)
    ).count()
    counts_returned["synthetic_grant_to_apps_eq_6thru8"] = synthetic_queryset.filter(
        Q(grant_count__gte=6) & Q(grant_count__lte=8)
    ).count()

    counts_returned["real_grant_to_apps_eq_9thru13"] = real_queryset.filter(
        Q(grant_count__gte=9) & Q(grant_count__lte=13)
    ).count()
    counts_returned["synthetic_grant_to_apps_eq_9thru13"] = synthetic_queryset.filter(
        Q(grant_count__gte=9) & Q(grant_count__lte=13)
    ).count()

    counts_returned["real_grant_to_apps_gt_13"] = real_queryset.filter(
        Q(grant_count__gt=13)
    ).count()
    counts_returned["synthetic_grant_to_apps_gt_13"] = synthetic_queryset.filter(
        Q(grant_count__gt=13)
    ).count()

    """
    Bene archived grants to applications break down count section
    """
    counts_returned["real_grant_archived_to_apps_eq_1"] = real_queryset.filter(
        Q(grant_archived_count=1)
    ).count()
    counts_returned[
        "synthetic_grant_archived_to_apps_eq_1"
    ] = synthetic_queryset.filter(Q(grant_archived_count=1)).count()

    counts_returned["real_grant_archived_to_apps_eq_2"] = real_queryset.filter(
        Q(grant_archived_count=2)
    ).count()
    counts_returned[
        "synthetic_grant_archived_to_apps_eq_2"
    ] = synthetic_queryset.filter(Q(grant_archived_count=2)).count()

    counts_returned["real_grant_archived_to_apps_eq_3"] = real_queryset.filter(
        Q(grant_archived_count=3)
    ).count()
    counts_returned[
        "synthetic_grant_archived_to_apps_eq_3"
    ] = synthetic_queryset.filter(Q(grant_archived_count=3)).count()

    counts_returned["real_grant_archived_to_apps_eq_4thru5"] = real_queryset.filter(
        Q(grant_archived_count__gte=4) & Q(grant_archived_count__lte=5)
    ).count()
    counts_returned[
        "synthetic_grant_archived_to_apps_eq_4thru5"
    ] = synthetic_queryset.filter(
        Q(grant_archived_count__gte=4) & Q(grant_archived_count__lte=5)
    ).count()

    counts_returned["real_grant_archived_to_apps_eq_6thru8"] = real_queryset.filter(
        Q(grant_archived_count__gte=6) & Q(grant_archived_count__lte=8)
    ).count()
    counts_returned[
        "synthetic_grant_archived_to_apps_eq_6thru8"
    ] = synthetic_queryset.filter(
        Q(grant_archived_count__gte=6) & Q(grant_archived_count__lte=8)
    ).count()

    counts_returned["real_grant_archived_to_apps_eq_9thru13"] = real_queryset.filter(
        Q(grant_archived_count__gte=9) & Q(grant_archived_count__lte=13)
    ).count()
    counts_returned[
        "synthetic_grant_archived_to_apps_eq_9thru13"
    ] = synthetic_queryset.filter(
        Q(grant_archived_count__gte=9) & Q(grant_archived_count__lte=13)
    ).count()

    counts_returned["real_grant_archived_to_apps_gt_13"] = real_queryset.filter(
        Q(grant_archived_count__gt=13)
    ).count()
    counts_returned[
        "synthetic_grant_archived_to_apps_gt_13"
    ] = synthetic_queryset.filter(Q(grant_archived_count__gt=13)).count()

    counts_returned["elapsed"] = round(datetime.utcnow().timestamp() - start_time, 3)

    return counts_returned


def get_beneficiary_grant_app_pair_counts():
    """
    Get DataAccessGrant and ArchivedDataAccessGrant counts
    for beneficiary<->application pairs.
    """

    # Init counts dict
    counts_returned = {}

    # Grant real/synth bene counts (includes granted to multiple apps)
    start_time = datetime.utcnow().timestamp()

    # Setup base queryset
    grant_queryset = DataAccessGrant.objects.values("beneficiary", "application")

    real_grant_queryset = grant_queryset.filter(
        ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).values("beneficiary", "application")

    synthetic_grant_queryset = grant_queryset.filter(
        Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).values("beneficiary", "application")

    counts_returned["grant_total"] = grant_queryset.count()
    counts_returned["real_grant"] = real_grant_queryset.count()
    counts_returned["synthetic_grant"] = synthetic_grant_queryset.count()

    # Setup base queryset
    grant_archived_queryset = ArchivedDataAccessGrant.objects.values(
        "beneficiary", "application"
    )

    real_grant_archived_queryset = grant_archived_queryset.filter(
        ~Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).values("beneficiary", "application")

    synthetic_grant_archived_queryset = grant_archived_queryset.filter(
        Q(beneficiary__crosswalk___fhir_id__startswith="-")
        & ~Q(beneficiary__crosswalk___fhir_id="")
        & Q(beneficiary__crosswalk___fhir_id__isnull=False)
    ).values("beneficiary", "application")

    # Get total table count
    counts_returned["grant_archived_total"] = grant_archived_queryset.count()
    counts_returned["real_grant_archived"] = real_grant_archived_queryset.count()
    counts_returned[
        "synthetic_grant_archived"
    ] = synthetic_grant_archived_queryset.count()

    """
    Bene<->App pair differences
    """
    # Pairs in Grant but not in ArchivedGrant.
    counts_returned["grant_vs_archived_difference_total"] = grant_queryset.difference(
        grant_archived_queryset
    ).count()
    counts_returned[
        "real_grant_vs_archived_difference_total"
    ] = real_grant_queryset.difference(real_grant_archived_queryset).count()
    counts_returned[
        "synthetic_grant_vs_archived_difference_total"
    ] = synthetic_grant_queryset.difference(synthetic_grant_archived_queryset).count()

    # Pairs in ArchivedGrant but not in Grant.
    counts_returned[
        "archived_vs_grant_difference_total"
    ] = grant_archived_queryset.difference(grant_queryset).count()
    counts_returned[
        "real_archived_vs_grant_difference_total"
    ] = real_grant_archived_queryset.difference(real_grant_queryset).count()
    counts_returned[
        "synthetic_archived_vs_grant_difference_total"
    ] = synthetic_grant_archived_queryset.difference(synthetic_grant_queryset).count()

    counts_returned["elapsed"] = round(datetime.utcnow().timestamp() - start_time, 3)

    return counts_returned
