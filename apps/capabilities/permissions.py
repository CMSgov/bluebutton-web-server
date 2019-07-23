import json
from django.core.exceptions import ImproperlyConfigured
from oauth2_provider.contrib.rest_framework import permissions
from .models import ProtectedCapability


class TokenHasProtectedCapability(permissions.TokenHasScope):

    def get_scopes(self, request, view):
        scopes = list(ProtectedCapability.objects.filter(
            protected_resources__contains=json.dumps([request.method, request.path])
        ).values_list('slug', flat=True).all())

        if (len(scopes) < 1):
            raise ImproperlyConfigured(
                "TokenHasProtectedCapability requires the method an path are referenced in at least one ProtectedCapability"
            )

        return scopes
