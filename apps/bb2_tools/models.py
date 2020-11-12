from apps.fhir.bluebutton.models import Crosswalk
from oauth2_provider.models import AccessToken, RefreshToken
from apps.dot_ext.models import Application, ArchivedToken


class DummyAdminObject(AccessToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Splunk dashboard"
        verbose_name_plural = "Splunk dashboards"


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
        verbose_name = "Access token (connected beneficiaries) count by apps"
        verbose_name_plural = "Access token (connected beneficiaries) count by apps"


class MyRefreshTokenViewer(RefreshToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"


class RefreshTokenStats(RefreshToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Refresh token count by apps"
        verbose_name_plural = "Refresh token count by apps"


class MyArchivedTokenViewer(ArchivedToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"


class ArchivedTokenStats(ArchivedToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Archived token count by apps"
        verbose_name_plural = "Archived token count by apps"


class ApplicationStats(Application):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Application stats"
        verbose_name_plural = "Application stats"
