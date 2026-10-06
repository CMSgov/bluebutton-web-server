import re

from corsheaders.signals import check_request_enabled
from django.conf import settings
from django.dispatch import receiver


@receiver(check_request_enabled)
def allow_any_origin_on_api_paths(sender, request, **kwargs):
    api_cors_urls_regex = getattr(settings, 'API_CORS_URLS_REGEX', None)
    return bool(api_cors_urls_regex and re.match(api_cors_urls_regex, request.path_info))
