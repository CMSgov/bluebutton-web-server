import json
import re

from rest_framework import permissions, status
from rest_framework.exceptions import APIException
from waffle import switch_is_active

from .models import ProtectedCapability


class BBCapabilitiesPermissionTokenScopeMissingException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class TokenHasProtectedCapability(permissions.BasePermission):

    def has_permission(self, request, view):
        token = request.auth

        if not token:
            return False

        if not switch_is_active("require-scopes"):
            return True

        if hasattr(token, "scope"):  # OAuth 2
            scopes = list(ProtectedCapability.objects.filter(
                slug__in=token.scope.split()
            ).values_list('protected_resources', flat=True).all())
            for scope in scopes:
                for method, path in json.loads(scope):
                    if method != request.method:
                        continue
                    if path == request.path:
                        return True
                    if re.fullmatch(path, request.path) is not None:
                        return True
            return False
        else:
            # BB2-237: Replaces ASSERT with exception. We should never reach here.
            mesg = ("TokenHasScope requires the `oauth2_provider.rest_framework.OAuth2Authentication`"
                    " authentication class to be used.")
            raise BBCapabilitiesPermissionTokenScopeMissingException(mesg)
