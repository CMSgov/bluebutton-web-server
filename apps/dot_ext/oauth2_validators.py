from oauth2_provider.oauth2_validators import OAuth2Validator as DotOAuth2Validator
from django.core.exceptions import ObjectDoesNotExist
from apps.pkce.oauth2_validators import PKCEValidatorMixin
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
