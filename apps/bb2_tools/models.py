from oauth2_provider.models import RefreshToken

# from oauth2_provider.models import RefreshToken, get_access_token_model
from apps.accounts.models import UserProfile
from apps.dot_ext.models import Application, ArchivedToken
from apps.fhir.bluebutton.models import Crosswalk

try:
    from oauth2_provider.models import get_access_token_model

    AccessToken = get_access_token_model()
except Exception:
    # App registry not ready yet — fall back to the default model class
    # This import path won't trigger the swap mechanism
    from oauth2_provider.models import AccessToken


class DummyAdminObject(AccessToken):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'
        verbose_name = 'Splunk dashboard'
        verbose_name_plural = 'Splunk dashboards'


class MyAccessTokenViewer(AccessToken):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'


class AccessTokenStats(AccessToken):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'
        verbose_name = 'Access token counts by apps'
        verbose_name_plural = 'Access token counts by apps'


class UserStats(UserProfile):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'
        verbose_name = 'User statistics'
        verbose_name_plural = 'User statistics'


class BeneficiaryDashboard(Crosswalk):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'


class MyRefreshTokenViewer(RefreshToken):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'


class RefreshTokenStats(RefreshToken):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'
        verbose_name = 'Refresh token counts by apps'
        verbose_name_plural = 'Refresh token counts by apps'


class MyArchivedTokenViewer(ArchivedToken):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'


class ArchivedTokenStats(ArchivedToken):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'
        verbose_name = 'Archived token counts by apps'
        verbose_name_plural = 'Archived token counts by apps'


class ApplicationStats(Application):
    class Meta:
        proxy = True
        app_label = 'bb2_tools'
        verbose_name = 'Application statistics'
        verbose_name_plural = 'Application statistics'
