from __future__ import absolute_import
from __future__ import unicode_literals

from oauth2_provider.settings import oauth2_settings

from oauthlib.oauth2.rfc6749.endpoints import Server as OAuthLibServer

from .models import ExpiresIn


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
    # settings.
    if expires_in is None:
        expires_in = oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS

    return expires_in


class Server(OAuthLibServer):
    def __init__(self, request_validator, token_expires_in=None,
                 token_generator=None, refresh_token_generator=None,
                 *args, **kwargs):
        super(Server, self).__init__(
            request_validator,
            token_expires_in=my_token_expires_in,  # add custom expires_in callable
            token_generator=token_generator,
            refresh_token_generator=refresh_token_generator,
            *args, **kwargs)
