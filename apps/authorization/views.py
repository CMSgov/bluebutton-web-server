from datetime import datetime

from django.db.models import Q
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import serializers
from rest_framework import status

from oauth2_provider.models import get_application_model
from oauth2_provider.contrib.rest_framework import TokenHasScope
from oauth2_provider.views.base import OAuthLibMixin
from oauth2_provider.views.generic import ClientProtectedResourceView

from apps.versions import VersionNotMatched, Versions
from apps.dot_ext.authentication import SLSAuthentication
from apps.authorization.models import DataAccessGrant
from apps.dot_ext.utils import get_application_from_meta, get_api_version_number_from_url
from apps.fhir.bluebutton.models import Crosswalk


Application = get_application_model()


class ApplicationSerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ('id', 'name', 'logo_uri', 'tos_uri', 'policy_uri', 'contacts')

    def get_contacts(self, obj):
        application = Application.objects.get(id=obj.id)
        return application.support_email or ""


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
        return DataAccessGrant.objects.select_related("application").filter(
            Q(expiration_date__gt=datetime.now()) | Q(expiration_date=None),
            beneficiary=self.request.user
        )


@method_decorator(csrf_exempt, name="dispatch")
class ExpireDataAccessGrantView(ClientProtectedResourceView, OAuthLibMixin):

    @staticmethod
    def post(request, *args, **kwargs):
        try:
            path_info = request.__dict__.get('path_info')
            version = get_api_version_number_from_url(path_info)
            patient_id = kwargs.pop('patient_id', None)

            # V1 is treated as the same as V2 since their pathways are very similar and use the same fhir_id_v2 despite the name
            match version:
                case Versions.V1:
                    user = Crosswalk.objects.get(fhir_id_v2=patient_id).user
                case Versions.V2:
                    user = Crosswalk.objects.get(fhir_id_v2=patient_id).user
                case Versions.V3:
                    user = Crosswalk.objects.get(fhir_id_v3=patient_id).user
                case _:
                    raise VersionNotMatched(f"{version} is not a valid version constant")

            client = get_application_from_meta(request)
            DataAccessGrant.objects.get(beneficiary=user.id, application=client).delete()
        except Crosswalk.DoesNotExist:
            return HttpResponse("Patient was Not Found. Please check the id number and try again.",
                                status=status.HTTP_404_NOT_FOUND)
        except DataAccessGrant.DoesNotExist:
            return HttpResponse("Data Access Grant was Not Found.",
                                status=status.HTTP_404_NOT_FOUND)

        return HttpResponse("success", status=status.HTTP_200_OK)
