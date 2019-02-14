import logging
from django.contrib.auth.models import User
from django.http import StreamingHttpResponse
from django.db.models import (
    Count,
    QuerySet,
    Min,
    Max,
)
from oauth2_provider.models import AccessToken
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    CharField,
    ListSerializer,
    IntegerField,
    DateTimeField,
    LIST_SERIALIZER_KWARGS,
)
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_csv.renderers import PaginatedCSVRenderer, CSVStreamingRenderer
from django_filters import rest_framework as filters
from ..accounts.models import UserProfile
from ..dot_ext.models import Application, ArchivedToken
from apps.authorization.models import (
    DataAccessGrant,
    ArchivedDataAccessGrant,
    check_grants,
    update_grants)
from apps.fhir.bluebutton.models import Crosswalk


log = logging.getLogger('hhs_server.%s' % __name__)

STREAM_SERIALIZER_KWARGS = LIST_SERIALIZER_KWARGS


class StreamingSerializer(ListSerializer):
    @property
    def data(self):
        data = self.instance
        psize = 100
        count = data.count() if isinstance(data, QuerySet) else len(data)
        log.info("csv of {} items".format(count))
        for i in range(0, count, psize):
            iterable = data.all()[i:i + psize] if isinstance(data, QuerySet) else data
            log.info("pulled {} items from the db starting at index {}".format(len(iterable), i))
            for item in iterable:
                yield self.child.to_representation(item)


class StreamableSerializerMixin(object):
    def __new__(cls, *args, **kwargs):

        # We override this method in order to automagically create
        # `ListSerializer` classes instead when `many=True` is set.
        if kwargs.pop('many', False):
            if kwargs.pop('stream', False):
                return cls.stream_init(*args, **kwargs)
            return cls.many_init(*args, **kwargs)

        return super().__new__(cls, *args, **kwargs)

    @classmethod
    def stream_init(cls, *args, **kwargs):
        allow_empty = kwargs.pop('allow_empty', None)
        child_serializer = cls(*args, **kwargs)
        stream_kwargs = {
            'child': child_serializer,
        }
        if allow_empty is not None:
            stream_kwargs['allow_empty'] = allow_empty

        stream_kwargs.update({
            key: value for key, value in kwargs.items()
            if key in STREAM_SERIALIZER_KWARGS
        })

        meta = getattr(cls, 'Meta', None)
        stream_serializer_class = getattr(meta, 'stream_serializer_class', StreamingSerializer)
        return stream_serializer_class(*args, **stream_kwargs)


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


class DevUserSerializer(StreamableSerializerMixin, ModelSerializer):
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


class ApplicationSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ('id', 'name', 'user', )


class BeneUserSerializer(StreamableSerializerMixin, ModelSerializer):
    user_type = CharField(source='userprofile.user_type')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'date_joined',
            'last_login',
            'user_type',
        )


class AppMetricsSerializer(ModelSerializer):
    beneficiaries = SerializerMethodField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ('id', 'name', 'active', 'user', 'beneficiaries', 'first_active', 'last_active',
                  'logo_uri', 'tos_uri', 'policy_uri', 'contacts', 'website_uri', 'description')

    def get_beneficiaries(self, obj):
        distinct = AccessToken.objects.filter(application=obj.id).distinct('user').values('user')

        real_cnt = Crosswalk.real_objects.filter(user__in=[item['user'] for item in distinct]).values('user', 'fhir_id').count()
        synth_cnt = Crosswalk.synth_objects.filter(user__in=[item['user'] for item in distinct]).values('user', 'fhir_id').count()

        return({'real': real_cnt, 'synthetic': synth_cnt})


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


class ArchivedTokenFilter(filters.FilterSet):
    class Meta:
        model = ArchivedToken
        fields = {
            'user': ['exact'],
            'application': ['exact'],
            'created': ['gte', 'lte'],
            'archived_at': ['gte', 'lte'],
            'token': ['exact'],
        }


class ArchivedTokenSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)
    application = ApplicationSerializer(read_only=True)

    class Meta:
        model = ArchivedToken
        fields = ('user', 'application', 'token', 'expires', 'created', 'archived_at', )


class ArchivedTokenView(ListAPIView):
    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, PaginatedCSVRenderer)
    serializer_class = ArchivedTokenSerializer
    pagination_class = MetricsPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ArchivedTokenFilter

    def get_queryset(self):

        queryset = ArchivedToken.objects.all().order_by('archived_at')

        return queryset


class ArchivedDataAccessGrantFilter(filters.FilterSet):
    class Meta:
        model = ArchivedDataAccessGrant
        fields = {
            'beneficiary': ['exact'],
            'application': ['exact'],
            'created_at': ['gte', 'lte'],
            'archived_at': ['gte', 'lte'],
        }


class ArchivedDataAccessGrantSerializer(ModelSerializer):
    beneficiary = UserSerializer(read_only=True)
    application = ApplicationSerializer(read_only=True)

    class Meta:
        model = ArchivedDataAccessGrant
        fields = ('beneficiary', 'application', 'created_at', 'archived_at', 'id', )


class ArchivedDataAccessGrantView(ListAPIView):
    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, PaginatedCSVRenderer)
    serializer_class = ArchivedDataAccessGrantSerializer
    pagination_class = MetricsPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ArchivedDataAccessGrantFilter

    def get_queryset(self):

        queryset = ArchivedDataAccessGrant.objects.all().order_by('archived_at')

        return queryset


class DataAccessGrantFilter(filters.FilterSet):
    class Meta:
        model = DataAccessGrant
        fields = {
            'beneficiary': ['exact'],
            'application': ['exact'],
            'created_at': ['gte', 'lte'],
        }


class DataAccessGrantSerializer(ModelSerializer):
    beneficiary = UserSerializer(read_only=True)
    application = ApplicationSerializer(read_only=True)

    class Meta:
        model = DataAccessGrant
        fields = ('beneficiary', 'application', 'created_at', 'id', )


class DataAccessGrantView(ListAPIView):
    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, PaginatedCSVRenderer)
    serializer_class = DataAccessGrantSerializer
    pagination_class = MetricsPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DataAccessGrantFilter

    def get_queryset(self):

        queryset = DataAccessGrant.objects.all()

        return queryset


class CheckDataAccessGrantsView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    def get(self, request, format=None):
        return Response(check_grants())

    def post(self, request, format=None):
        return Response(update_grants())


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
        queryset = Application.objects.select_related().all().order_by('name')
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


class DevelopersStreamView(ListAPIView):
    permission_classes = (
        IsAuthenticated,
        IsAdminUser,
    )

    queryset = queryset = User.objects.select_related().filter(userprofile__user_type='DEV').annotate(
        app_count=Count('dot_ext_application'),
        first_active=Min('dot_ext_application__first_active'),
        active_app_count=Count('dot_ext_application__first_active'),
        last_active=Max('dot_ext_application__last_active')).all()

    serializer_class = DevUserSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DeveloperFilter
    renderer_classes = (CSVStreamingRenderer,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True, stream=True)
        renderer = CSVStreamingRenderer()
        response = StreamingHttpResponse(renderer.render(serializer.data), content_type='text/csv')
        return response
