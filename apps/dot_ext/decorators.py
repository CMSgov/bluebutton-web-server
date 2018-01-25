from __future__ import absolute_import
from __future__ import unicode_literals

from functools import wraps

from django.http import JsonResponse

from oauthlib.oauth2 import Server

from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.oauth2_backends import OAuthLibCore


def require_valid_token():
    def decorator(view_func):
        @wraps(view_func)
        def _validate(request, *args, **kwargs):
            core = OAuthLibCore(Server(OAuth2Validator()))
            valid, oauthlib_req = core.verify_request(request, scopes=[])
            if valid:
                request.resource_owner = oauthlib_req.user
                return view_func(request, *args, **kwargs)

            return JsonResponse({
                                "error": {
                                    "code": 401,
                                    "message": "The token authentication failed.",
                                }},
                                status=401)

        return _validate

    return decorator
