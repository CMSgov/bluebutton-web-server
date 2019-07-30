import json
from waffle import switch_is_active
from django.core.exceptions import ImproperlyConfigured
from oauth2_provider.contrib.rest_framework import permissions
from .models import ProtectedCapability


class TokenHasProtectedCapability(permissions.TokenHasScope):

    def has_permission(self, request, view):
        if not switch_is_active("require-scopes"):
            return True
        return super().has_permission(request, view)


    def get_scopes(self, request, view):
        scopes = list(ProtectedCapability.objects.filter(
            protected_resources__contains=json.dumps([request.method, request.path])
        ).values_list('slug', flat=True).all())

        if (len(scopes) < 1):
            raise ImproperlyConfigured(
                "TokenHasProtectedCapability requires the method an path are referenced in at least one ProtectedCapability"
            )

        return scopes
