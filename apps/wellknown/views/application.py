from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from apps.dot_ext.models import Application, ApplicationLabel
from ..serializers import ApplicationListSerializer, ApplicationLabelSerializer


class ApplicationListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10000


class LabelSlugFilter(CharFilter):
    def filter(self, qs, value):
        result_qs = Application.objects.none()
        if value:
            slugs = [slug.strip() for slug in value.split(',')]
            for slug in slugs:
                # Check if label slug is valid
                if not ApplicationLabel.objects.exclude(slug__in=settings.APP_LIST_EXCLUDE).filter(slug=slug).exists():
                    raise serializers.ValidationError(detail='Invalid slug name for label parameter:  %s' % (slug), code=400)
                # Concatinate filter query results
                result_qs = result_qs | super().filter(qs, slug)
        else:
            result_qs = super().filter(qs, value)
        return result_qs.distinct()


class ApplicationFilter(FilterSet):
    label = LabelSlugFilter(field_name="applicationlabel__slug")

    class Meta:
        model = Application
        fields = ['label']


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
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ApplicationFilter

    def get_queryset(self):
        queryset = Application.objects.exclude(active=False).exclude(
            applicationlabel__slug__in=settings.APP_LIST_EXCLUDE).order_by('name')
        return queryset


class ApplicationLabelView(ListAPIView):
    """
    View to provide an application labels list.

    An application label that has a label slug in the APP_LIST_EXCLUDE
    list will be excluded from this view.
    """
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer,)
    serializer_class = ApplicationLabelSerializer

    def get_queryset(self):
        queryset = ApplicationLabel.objects.exclude(
            slug__in=settings.APP_LIST_EXCLUDE).order_by('name')
        return queryset
