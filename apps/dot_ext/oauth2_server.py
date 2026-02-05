from datetime import timedelta
from waffle import switch_is_active
from oauthlib.oauth2.rfc6749.endpoints import Server as OAuthLibServer
from oauth2_provider.settings import oauth2_settings

from .models import ExpiresIn
from ..pkce.oauth2_server import PKCEServerMixin


def my_token_expires_in(request):
    """
    Function that returns the expires_in value used to create
    tokens.
    """
    # first we try to retrieve the expires_in from the ExpiresIn
    # table.
    client_id = request.client.client_id
    user_id = request.user.pk
    expires_in = ExpiresIn.objects.get_expires_in(client_id, user_id)
    # if no record is found we default to the value defined in the
    # oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS
    # Otherwise, we'll use one hour
    if expires_in is None:
        if switch_is_active("one_hour_token_expiry"):
            one_hour_delta = timedelta(hours=1)
            seconds_in_one_hour = int(one_hour_delta.total_seconds())
            expires_in = seconds_in_one_hour
        else:
            expires_in = oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS

    return expires_in


class Server(PKCEServerMixin, OAuthLibServer):
    def __init__(self, request_validator, token_expires_in=None,
                 token_generator=None, refresh_token_generator=None,
                 *args, **kwargs):
        super(Server, self).__init__(
            request_validator,
            token_expires_in=my_token_expires_in,  # add custom expires_in callable
            token_generator=token_generator,
            refresh_token_generator=refresh_token_generator,
            *args, **kwargs)
