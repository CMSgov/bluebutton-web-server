from datetime import timedelta
from urllib.parse import parse_qs

from oauth2_provider.settings import oauth2_settings
from oauthlib.oauth2.rfc6749.endpoints import Server as OAuthLibServer
from waffle import switch_is_active

from apps.constants import CLIENT_CREDENTIALS
from apps.pkce.oauth2_server import PKCEServerMixin


def my_token_expires_in(request):
    """
    Function that returns the expires_in value used to create
    tokens.
    """
    request_body = parse_qs(request.body)
    grant_type = request_body.get('grant_type', [None])

    if switch_is_active('one_hour_token_expiry') or (grant_type[0] and grant_type[0] == CLIENT_CREDENTIALS):
        one_hour_delta = timedelta(hours=1)
        seconds_in_one_hour = int(one_hour_delta.total_seconds())
        return seconds_in_one_hour
    else:
        return oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS


class Server(PKCEServerMixin, OAuthLibServer):
    def __init__(
        self,
        request_validator,
        token_expires_in=None,
        token_generator=None,
        refresh_token_generator=None,
        *args,
        **kwargs,
    ):
        super(Server, self).__init__(
            request_validator,
            token_expires_in=my_token_expires_in,  # add custom expires_in callable
            token_generator=token_generator,
            refresh_token_generator=refresh_token_generator,
            *args,
            **kwargs,
        )
