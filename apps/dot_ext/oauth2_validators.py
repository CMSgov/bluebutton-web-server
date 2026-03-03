from django.core.exceptions import ObjectDoesNotExist
from oauth2_provider.oauth2_validators import OAuth2Validator as DotOAuth2Validator
from oauthlib.oauth2.rfc6749 import utils
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from typing import Any, List

from apps.dot_ext.scopes import CapabilitiesScopes
from apps.pkce.oauth2_validators import PKCEValidatorMixin


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

    def is_within_original_scope(
        self,
        request_scopes: List[str],
        refresh_token: str,
        request: Any,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Determine if the requested scopes are within the original scopes of the access token.
        This overrides a function from OAuth2Validator to ensure that when a client makes a refresh
        token request with a subset of the original scopes, that is allowed as long as the scopes are
        valid subscopes of the originally granted scopes.

        Args:
            request_scopes (List[str]): The scopes requested in the current refresh token request
            refresh_token (str): The refresh token for the current access token
            request (Any): The Django request object
            args (Any): Additional positional arguments
            kwargs (Any): Additional keyword arguments

        Returns:
            bool: Whether or not the requested scopes are within the original scopes of the access token
        """

        original_scopes = utils.scope_to_list(
            self.get_original_scopes(refresh_token, request)
        )

        for req_scope in request_scopes:
            if not CapabilitiesScopes().is_smart_subscope(req_scope, original_scopes):
                return False
        return True


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
