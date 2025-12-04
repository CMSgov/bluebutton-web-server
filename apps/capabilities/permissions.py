import json
import re

from apps.dot_ext.scopes import CapabilitiesScopes
from rest_framework import permissions, status
from rest_framework.exceptions import APIException, ParseError
from waffle import switch_is_active

from .models import ProtectedCapability

import apps.logging.request_logger as logging

logger = logging.getLogger(logging.DEBUG_GENERAL)


class BBCapabilitiesPermissionTokenScopeMissingException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class TokenHasProtectedCapability(permissions.BasePermission):

    def has_permission(self, request, view) -> bool:  # type: ignore
        logger.warning({"has_permission": "start"})
        token = request.auth
        access_token_query_param = request.GET.get("access_token", None)

        if access_token_query_param is not None:
            raise ParseError(
                "Using the access token in the query parameters is not supported. "
                "Use the Authorization header instead"
            )

        if not token:
            logger.warning("has_permission: not token")
            return False

        if not switch_is_active("require-scopes"):
            logger.warning("has_permission: switch_is_active('require-scopes')")
            return True

        if hasattr(token, "scope"):  # OAuth 2
            token_scopes = token.scope.split()

            if switch_is_active("enable_coverage_only"):
                if "coverage-eligibility" in request.auth.application.get_internal_application_labels():
                    token_scopes = CapabilitiesScopes().remove_eob_scopes(token_scopes)

            scopes = list(ProtectedCapability.objects.filter(
                slug__in=token_scopes
            ).values_list('protected_resources', flat=True).all())

            logger.warning({"token_scopes": token_scopes, "scopes": scopes})

            for scope in scopes:
                for method, path in json.loads(scope):
                    logger.warning({"scope in scopes": scope,
                                    "method": method,
                                    "path": path,
                                    "request.method": request.method,
                                    "request.path": request.path})
                    if method != request.method:
                        logger.warning({"A": 1})
                        logger.warning({"request_method": request.method})
                        continue
                    if path == request.path:
                        logger.warning({"A": 2})
                        logger.warning({"path == request.path": (path == request.path)})
                        return True
                    if re.fullmatch(path, request.path) is not None:
                        logger.warning({"A": 3})
                        return True
                    logger.warning({"end-of-scope-in-scopes loop": "here"})

            logger.warning("has_permission: scope not matched/found")
            return False
        else:
            # BB2-237: Replaces ASSERT with exception. We should never reach here.
            mesg = ("TokenHasScope requires the `oauth2_provider.rest_framework.OAuth2Authentication`"
                    " authentication class to be used.")
            logger.warning("has_permission: end of line scope missing exception")
            raise BBCapabilitiesPermissionTokenScopeMissingException(mesg)
