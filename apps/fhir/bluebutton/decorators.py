from __future__ import absolute_import
from __future__ import unicode_literals

from functools import wraps

from oauthlib.oauth2 import Server

from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.oauth2_backends import OAuthLibCore

from .errors import build_error_response


def require_valid_token():
    def decorator(view_func):
        @wraps(view_func)
        def _validate(request, *args, **kwargs):
            core = OAuthLibCore(Server(OAuth2Validator()))
            valid, oauthlib_req = core.verify_request(request, scopes=[])
            if valid:
                # Note, resource_owner is not a very good name for this
                request.resource_owner = oauthlib_req.user
                request.oauth = oauthlib_req
                import pdb; pdb.set_trace()
                return view_func(request, *args, **kwargs)

            return build_error_response(401, 'The token authentication failed.')

        return _validate

    return decorator
