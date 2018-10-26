from django.contrib.auth.models import User
from django.db.models import Count, Min, Max
from oauth2_provider.models import AccessToken
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    CharField,
    IntegerField,
    DateTimeField,
)
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_csv.renderers import PaginatedCSVRenderer
from django_filters import rest_framework as filters
from ..accounts.models import UserProfile
from ..dot_ext.models import Application


class UserSerializer(ModelSerializer):
    organization = CharField(source='userprofile.organization_name')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'date_joined',
            'last_login',
            'organization',
        )


class DevUserSerializer(ModelSerializer):
    organization = CharField(source='userprofile.organization_name')
    user_type = CharField(source='userprofile.user_type')
    app_count = IntegerField()
    first_active = DateTimeField()
    last_active = DateTimeField()
    active_app_count = IntegerField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'date_joined',
            'last_login',
            'organization',
            'user_type',
            'app_count',
            'first_active',
            'last_active',
            'active_app_count',
        )


class AppMetricsSerializer(ModelSerializer):

    beneficiaries = SerializerMethodField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ('id', 'name', 'active', 'user', 'beneficiaries', 'first_active', 'last_active')

    def get_beneficiaries(self, obj):
        return({'count': AccessToken.objects.filter(application=obj.id).distinct('user').count()})


class MetricsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10000


class BeneMetricsView(APIView):
    """
    View to provide beneficiary metrics.

    * Only admin users are able to access this view.
    * Default returns count info
    """
    permission_classes = (
        IsAuthenticated,
        IsAdminUser,
    )

    renderer_classes = (JSONRenderer, )

    def get(self, request, format=None):
        content = {
            'count': UserProfile.objects.filter(user_type='BEN').count()
        }
        return Response(content)


class AppMetricsView(ListAPIView):
    """
    View to provide application metrics.


    * Only admin users are able to access this view
    * Default returns count info and application list data with unique bene counts
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, PaginatedCSVRenderer)
    serializer_class = AppMetricsSerializer
    pagination_class = MetricsPagination

    def get_queryset(self):

        queryset = Application.objects.all().order_by('name')

        return queryset


class AppMetricsDetailView(APIView):
    """
    View to provide application metrics detail.


    * Only admin users are able to access this view
    * Default returns count info and application list data with unique bene count
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, pk, format=None):

        queryset = Application.objects.get(pk=pk)

        return Response(AppMetricsSerializer(queryset).data)


class TokenMetricsView(APIView):
    """
    View to provide access token metrics.

    * Only admin users are able to access this view.
    * Default returns count info
    """
    permission_classes = (
        IsAuthenticated,
        IsAdminUser,
    )

    renderer_classes = (JSONRenderer, )

    def get(self, request, format=None):
        content = {
            'count': AccessToken.objects.count()
        }
        return Response(content)


class DeveloperFilter(filters.FilterSet):
    joined_after = filters.DateFilter(field_name="date_joined", lookup_expr='gte')
    joined_before = filters.DateFilter(field_name="date_joined", lookup_expr='lte')
    app_count = filters.NumberFilter(
        field_name="app_count",
        label="Application Count")
    min_app_count = filters.NumberFilter(
        field_name="app_count",
        lookup_expr='gte',
        label="Min Application Count")
    max_app_count = filters.NumberFilter(
        field_name="app_count",
        lookup_expr='lte',
        label="Max Application Count")

    first_active_after = filters.DateFilter(
        label="Date first_active is greater than or equal to",
        field_name="first_active",
        lookup_expr='gte')
    first_active_before = filters.DateFilter(
        label="Date first_active is less than or equal to",
        field_name="first_active",
        lookup_expr='lte')

    last_active_after = filters.DateFilter(
        label="Date last_active is greater than or equal to",
        field_name="last_active",
        lookup_expr='gte')
    last_active_before = filters.DateFilter(
        label="Date last_active is less than or equal to",
        field_name="last_active",
        lookup_expr='lte')

    active_app_count = filters.NumberFilter(
        field_name="active_app_count",
        label="Active Application Count")
    min_active_app_count = filters.NumberFilter(
        field_name="active_app_count",
        lookup_expr='gte',
        label="Min Active Application Count")
    max_active_app_count = filters.NumberFilter(
        field_name="active_app_count",
        lookup_expr='lte',
        label="Max Active Application Count")

    class Meta:
        model = User
        fields = ['joined_after', 'joined_before', 'app_count', 'min_app_count', 'max_app_count',
                  'first_active_after', 'first_active_before', 'last_active_after', 'last_active_before',
                  'active_app_count', 'min_active_app_count', 'max_active_app_count']


class DevelopersView(ListAPIView):
    permission_classes = (
        IsAuthenticated,
        IsAdminUser,
    )

    queryset = User.objects.select_related().filter(userprofile__user_type='DEV').annotate(
        app_count=Count('dot_ext_application'),
        first_active=Min('dot_ext_application__first_active'),
        active_app_count=Count('dot_ext_application__first_active'),
        last_active=Max('dot_ext_application__last_active')).all()

    serializer_class = DevUserSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DeveloperFilter
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, PaginatedCSVRenderer)
    pagination_class = MetricsPagination
