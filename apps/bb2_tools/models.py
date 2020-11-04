from apps.fhir.bluebutton.models import Crosswalk
from oauth2_provider.models import get_access_token_model
from oauth2_provider.models import AccessToken, RefreshToken
from apps.dot_ext.models import ArchivedToken


class DummyAdminObject(AccessToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Splunk Dashboard"
        verbose_name_plural = "Splunk Dashboards"


class BeneficiaryDashboard(Crosswalk):

    class Meta:
        proxy = True
        app_label = "bb2_tools"

    @property
    def access_tokens(self):
        AccessToken = get_access_token_model()
        tokens = AccessToken.objects.filter(user=self.user).all()
        return tokens


class MyAccessTokenViewer(AccessToken):
    class Meta:
        proxy = True
        app_label = "bb2_tools"


class AccessTokenStats(AccessToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Access Token (Connected Beneficiaries) Count By Apps"
        verbose_name_plural = "Access Token (Connected Beneficiaries) Count By Apps"


class MyRefreshTokenViewer(RefreshToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"


class RefreshTokenStats(RefreshToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Refresh Token Count By Apps"
        verbose_name_plural = "Refresh Token Count By Apps"


class MyArchivedTokenViewer(ArchivedToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"


class ArchivedTokenStats(ArchivedToken):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
        verbose_name = "Archived Token Count By Apps"
        verbose_name_plural = "Archived Token Count By Apps"


class MyConnectedApplicationViewer(Crosswalk):

    class Meta:
        proxy = True
        app_label = "bb2_tools"
