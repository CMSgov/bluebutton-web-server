from django.urls import re_path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import OpenAPI

urlpatterns = format_suffix_patterns(
    [re_path(r"^openapi", OpenAPI.as_view())],
    allowed=["json", "yaml"],
    suffix_required=True,
)
