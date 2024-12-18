from django.db import models
from oauth2_provider.models import AccessToken, RefreshToken

from apps.accounts.models import UserProfile
from apps.dot_ext.models import Application, ArchivedToken
from apps.fhir.bluebutton.models import Crosswalk


class DummyAdminObject(AccessToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Splunk dashboard"
        verbose_name_plural = "Splunk dashboards"


class UserStats(UserProfile):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "User statistics"
        verbose_name_plural = "User statistics"


class BeneficiaryDashboard(Crosswalk):

    class Meta:
        proxy = True
        app_label = "bb2_tools"


class MyAccessTokenViewer(AccessToken):
    class Meta:
        proxy = True
        app_label = "bb2_tools"


class AccessTokenStats(AccessToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Access token counts by apps"
        verbose_name_plural = "Access token counts by apps"


class MyRefreshTokenViewer(RefreshToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"


class RefreshTokenStats(RefreshToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Refresh token counts by apps"
        verbose_name_plural = "Refresh token counts by apps"


class MyArchivedTokenViewer(ArchivedToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"


class ArchivedTokenStats(ArchivedToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Archived token counts by apps"
        verbose_name_plural = "Archived token counts by apps"


class ApplicationStats(Application):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Application statistics"
        verbose_name_plural = "Application statistics"


class SyntheticBeneficiary(models.Model):
    beneficiary_id = models.CharField(
        max_length=80,
        null=False,
        unique=True,
        default=None,
        db_column="fhir_id",
        db_index=True,
    )
    mbi_unhashed = models.CharField(
        max_length=11,
        verbose_name="Unhashed MBI",
        unique=True,
        null=False,
        default=None,
        db_column="user_mbi",
        db_index=True,
    )
    medicaid_un = models.TextField(null=False)
    medicaid_pw = models.TextField(null=False)
    age = models.IntegerField(null=False)
    first_name = models.TextField(null=False)
    last_name = models.TextField(null=False)
    address_1 = models.TextField(null=False)
    address_2 = models.TextField(blank=True, null=True)
    city = models.TextField(null=False)
    state = models.TextField(null=False)
    postal_code = models.TextField(null=False)
    part_d_contract_number = models.TextField(blank=True, null=True)
    carrier_claims_total = models.IntegerField(default=0)
    dme_claims_total = models.IntegerField(default=0)
    hha_claims_total = models.IntegerField(default=0)
    hospice_claims_total = models.IntegerField(default=0)
    inpatient_claims_total = models.IntegerField(default=0)
    outpatient_claims_total = models.IntegerField(default=0)
    snf_claims_total = models.IntegerField(default=0)

    @property
    def part_d_events_total(self):
        return self.carrier_claims_total + \
            self.dme_claims_total + \
            self.hha_claims_total + \
            self.hospice_claims_total + \
            self.inpatient_claims_total + \
            self.outpatient_claims_total + \
            self.snf_claims_total


class SyntheticBeneficiaryFilter(SyntheticBeneficiary):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Synthetic Beneficiary Filter"
        verbose_name_plural = "Synthetic Beneficiary Filters"
