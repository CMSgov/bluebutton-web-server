from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from oauth2_provider.models import get_application_model
from oauth2_provider.contrib.rest_framework import TokenHasScope
from apps.dot_ext.authentication import SLSAuthentication
from .models import DataAccessGrant
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


class ExpireDataAccessGrantView(APIView):
    authentication_classes = [SLSAuthentication]

    @staticmethod
    def post(request, *args, **kwargs):
        try:
            patient_id = kwargs.pop('patient_id', None)
            client_id = request.POST.get('client_id', '')
            user = Crosswalk.objects.get(_fhir_id=patient_id).user
            application = Application.objects.get(client_id=client_id)
            DataAccessGrant.objects.get(beneficiary=user.id, application=application.id).delete()
        except NotFound:
            raise
        except Exception:
            raise
        return Response("success", status=status.HTTP_200_OK)
