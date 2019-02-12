from ...dot_ext.models import Application
from ..serializers import ApplicationListSerializer
from django.conf import settings
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer


class ApplicationListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10000


class ApplicationListView(ListAPIView):
    """
    View to provide an applications list.

    An application that has active=False or with a label slug in the APP_LIST_EXCLUDE
    list will be excluded from this view.
    """
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer,)
    serializer_class = ApplicationListSerializer
    pagination_class = ApplicationListPagination

    def get_queryset(self):
        queryset = Application.objects.exclude(active=False).exclude(
            applicationlabel__slug__in=settings.APP_LIST_EXCLUDE).order_by('name')
        return queryset
