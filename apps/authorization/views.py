from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from oauth2_provider.models import get_application_model
from oauth2_provider.contrib.rest_framework import TokenHasScope
from oauth2_provider.views.base import OAuthLibMixin
from oauth2_provider.views.generic import ClientProtectedResourceView
from apps.dot_ext.authentication import SLSAuthentication
from .models import DataAccessGrant
from ..dot_ext.utils import get_application_from_meta
from ..fhir.bluebutton.models import Crosswalk

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


class ExpireDataAccessGrantView(ClientProtectedResourceView, OAuthLibMixin):

    @staticmethod
    def post(request, *args, **kwargs):
        try:
            patient_id = kwargs.pop('patient_id', None)
            user = Crosswalk.objects.get(_fhir_id=patient_id).user
            client = get_application_from_meta(request)
            DataAccessGrant.objects.get(beneficiary=user.id, application=client).delete()
        except NotFound:
            raise
        except Exception:
            raise
        return HttpResponse("success", status=status.HTTP_200_OK)
