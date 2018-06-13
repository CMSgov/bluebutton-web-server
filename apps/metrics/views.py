from django.db.models import Count
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken
from rest_framework.serializers import BooleanField, CharField, IntegerField, ModelSerializer
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from ..accounts.models import UserProfile
from ..dot_ext.models import Application


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class AppMetricsSerializer(ModelSerializer):

    beneficiaries = IntegerField(source='accesstoken__user__count', read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ('id', 'name', 'active', 'user', 'beneficiaries')

        queryset = Application.objects.all().annotate(Count('accesstoken__user', distinct=True)).order_by('name')

class AppMetricsPagination(PageNumberPagination):
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

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    serializer_class = AppMetricsSerializer

    pagination_class = AppMetricsPagination

    def get_queryset(self):

        queryset = Application.objects.all().annotate(Count('accesstoken__user', distinct=True)).order_by('name')

        return queryset


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
