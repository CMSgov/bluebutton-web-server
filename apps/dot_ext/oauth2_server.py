from datetime import timedelta

from oauthlib.oauth2.rfc6749.endpoints import Server as OAuthLibServer

from apps.pkce.oauth2_server import PKCEServerMixin


def my_token_expires_in(request):
    """
    Function that returns the expires_in value used to create
    tokens.
    """
    one_hour_delta = timedelta(hours=1)
    seconds_in_one_hour = int(one_hour_delta.total_seconds())
    return seconds_in_one_hour


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
