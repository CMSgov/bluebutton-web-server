from rest_framework import permissions, status
from rest_framework.exceptions import APIException, ParseError
from waffle import switch_is_active

from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.scopes import CapabilitiesScopes
from apps.utils import is_valid_scope


class BBCapabilitiesPermissionTokenScopeMissingException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class TokenHasProtectedCapability(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:  # type: ignore
        token = request.auth
        access_token_query_param = request.GET.get('access_token', None)

        if access_token_query_param is not None:
            raise ParseError(
                'Using the access token in the query parameters is not supported. Use the Authorization header instead'
            )

        if not token:
            return False

        if not switch_is_active('require-scopes'):
            return True

        if hasattr(token, 'scope'):  # OAuth 2
            token_scopes = token.scope.split()

            if switch_is_active('enable_coverage_only'):
                if 'coverage-eligibility' in request.auth.application.get_internal_application_labels():
                    token_scopes = CapabilitiesScopes().remove_eob_scopes(token_scopes)

            scopes = list(
                ProtectedCapability.objects.filter(slug__in=token_scopes)
                .values_list('protected_resources', flat=True)
                .all()
            )

            is_valid = is_valid_scope(scopes, request)
            return is_valid

        else:
            # BB2-237: Replaces ASSERT with exception. We should never reach here.
            mesg = (
                'TokenHasScope requires the `oauth2_provider.rest_framework.OAuth2Authentication`'
                ' authentication class to be used.'
            )
            raise BBCapabilitiesPermissionTokenScopeMissingException(mesg)
