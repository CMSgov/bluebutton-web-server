from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import serializers
from oauth2_provider.models import AccessToken
from oauth2_provider.contrib.rest_framework import TokenHasScope
from apps.dot_ext.authentication import SLSAuthentication
from ..models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('id', 'name', 'logo_uri', 'tos_uri', 'policy_uri', 'contacts')


class AccessTokenSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer(read_only=True)

    class Meta:
        model = AccessToken
        fields = ('id', 'user', 'application')


class AuthorizedTokens(viewsets.GenericViewSet,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin):

    authentication_classes = [SLSAuthentication]
    permission_classes = [TokenHasScope]
    required_scopes = ['token_management']
    serializer_class = AccessTokenSerializer

    def get_queryset(self):
        return AccessToken.objects.select_related("application").filter(user=self.request.user)
