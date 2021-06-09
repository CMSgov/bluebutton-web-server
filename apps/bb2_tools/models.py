from django.contrib.auth.models import User
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


class V2User(User):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "V2 User"
        verbose_name_plural = "V2 Users"
