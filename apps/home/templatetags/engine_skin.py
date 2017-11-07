from django import template
from django.conf import settings
register = template.Library()


@register.simple_tag
def skin_static(file_ref):
    skinned_file_ref = settings.STATIC_URL + file_ref
    return skinned_file_ref
