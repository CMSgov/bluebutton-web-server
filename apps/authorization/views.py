from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import serializers
from oauth2_provider.models import get_application_model
from oauth2_provider.contrib.rest_framework import TokenHasScope
from apps.dot_ext.authentication import SLSAuthentication
from .models import DataAccessGrant

Application = get_application_model()


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('id', 'name', 'logo_uri', 'tos_uri', 'policy_uri', 'contacts')


class DataAccessGrantSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True, source='beneficiary')

    class Meta:
        model = DataAccessGrant
        fields = ('id', 'application', 'user')


class AuthorizedGrants(viewsets.GenericViewSet,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin):

    authentication_classes = [SLSAuthentication]
    permission_classes = [TokenHasScope]
    required_scopes = ['token_management']
    serializer_class = DataAccessGrantSerializer

    def get_queryset(self):
        return DataAccessGrant.objects.select_related("application").filter(beneficiary=self.request.user)
