from oauthlib.oauth2.rfc6749.endpoints import Server as OAuthLibServer

from apps.dot_ext.constants import SECONDS_IN_ONE_HOUR
from apps.pkce.oauth2_server import PKCEServerMixin


def my_token_expires_in(request):
    """
    Function that returns the expires_in value used to create
    tokens.
    """
    return SECONDS_IN_ONE_HOUR


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
