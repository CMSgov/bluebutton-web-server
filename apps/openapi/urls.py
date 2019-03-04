from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from .views import OpenAPI


urlpatterns = format_suffix_patterns(
    [url(r'^openapi', OpenAPI.as_view())],
    allowed=['json', 'yaml'],
    suffix_required=True)
