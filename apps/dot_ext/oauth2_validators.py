from oauth2_provider.oauth2_validators import OAuth2Validator as DotOAuth2Validator
from django.core.exceptions import ObjectDoesNotExist
from apps.pkce.oauth2_validators import PKCEValidatorMixin
from oauthlib.oauth2.rfc6749 import utils
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError


class OAuth2Validator(DotOAuth2Validator):
    def _extract_basic_auth(self, request):
        """
        This overrided method additionally checks the "Authorization" header
        for compatability.
        TODO: Remove this if it becomes possible.
        """
        auth = request.headers.get("HTTP_AUTHORIZATION", None)
        if not auth:
            auth = request.headers.get("Authorization", None)
        if not auth:
            return None

        splitted = auth.split(" ", 1)
        if len(splitted) != 2:
            return None
        auth_type, auth_string = splitted

        if auth_type != "Basic":
            return None

        return auth_string

    def is_within_original_scope(self, request_scopes, refresh_token, request, *args, **kwargs):
        """
        Handle SMART v2 granular scope downscoping.
        e.g. patient/Patient.r is a valid subset of patient/Patient.rs
        """
        original_scopes = utils.scope_to_list(
            self.get_original_scopes(refresh_token, request)
        )
        print("original_scopes: ", original_scopes)
        for req_scope in request_scopes:
            if not self._is_smart_subscope(req_scope, original_scopes):
                return False
        return True

    def _is_smart_subscope(self, requested, original_list):
        """
        Check if `requested` is a valid SMART v2 subscope of any scope in original_list.
        e.g. 'patient/Patient.r' is a subscope of 'patient/Patient.rs'
        """
        # First try exact match
        if requested in original_list:
            return True

        # Try SMART v2 granular subscope: same resource, requested permissions subset of original
        # Format: (patient|user|system)/ResourceType.(r|c|u|d|s)+
        for orig in original_list:
            if self._smart_scope_contains(orig, requested):
                return True
        return False

    def _smart_scope_contains(self, original, requested):
        """
        Returns True if `requested` scope is a subset of `original` scope.
        e.g. original='patient/Patient.rs', requested='patient/Patient.r' → True
        """
        # Split into context/resource and permissions
        try:
            orig_resource, orig_perms = original.rsplit('.', 1)
            req_resource, req_perms = requested.rsplit('.', 1)
        except ValueError:
            return False

        # Resource part must match exactly
        if orig_resource != req_resource:
            return False

        # All requested permission chars must be present in original
        valid_chars = set('rcuds')
        orig_perm_set = set(orig_perms) & valid_chars
        req_perm_set = set(req_perms) & valid_chars

        return req_perm_set.issubset(orig_perm_set)


class SingleAccessTokenValidator(
        PKCEValidatorMixin,
        OAuth2Validator,
):
    """
    This custom oauth2 validator checks if a valid token
    exists for the current user/application and return
    it instead of creating a new one.
    """
    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        if redirect_uri is None:
            # Set to default
            redirect_uri = client.default_redirect_uri

        return super(SingleAccessTokenValidator, self).confirm_redirect_uri(
            client_id,
            code,
            redirect_uri,
            client,
            *args,
            **kwargs)

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        try:
            return super().get_original_scopes(refresh_token, request, *args, **kwargs)
        except ObjectDoesNotExist:
            raise InvalidGrantError
