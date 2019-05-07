from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, Filter, BaseInFilter
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


class LabelSlugValidator:
    def __call__(self, value):
        if value:
            if not ApplicationLabel.objects.exclude(slug__in=settings.APP_LIST_EXCLUDE).filter(slug=value).exists():
                raise ValidationError('Invalid slug name for label parameter:  %s' % (value), code=400)


class LabelSlugField(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(validators=[LabelSlugValidator()], **kwargs)


class LabelSlugFilter(BaseInFilter, Filter):
    field_class = LabelSlugField


class ApplicationListFilter(FilterSet):
    label = LabelSlugFilter(field_name="applicationlabel__slug", lookup_expr='in')

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
    filterset_class = ApplicationListFilter

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
