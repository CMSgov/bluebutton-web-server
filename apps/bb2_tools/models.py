from apps.fhir.bluebutton.models import Crosswalk
from oauth2_provider.models import get_access_token_model
from oauth2_provider.models import AccessToken, RefreshToken
from apps.dot_ext.models import ArchivedToken


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


class MyRefreshTokenViewer(RefreshToken):
    class Meta:
        proxy = True
        app_label = "bb2_tools"


class MyArchivedTokenViewer(ArchivedToken):
    class Meta:
        proxy = True
        app_label = "bb2_tools"
