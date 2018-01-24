from __future__ import absolute_import
from __future__ import unicode_literals

from functools import wraps

from django.http import HttpResponseForbidden, JsonResponse

from oauthlib.oauth2 import Server

from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.oauth2_backends import OAuthLibCore

from .permissions import allow_resource


def capability_protected_resource(scopes=None, validator_cls=OAuth2Validator, server_cls=Server):
    """
    Decorator to protect views by providing OAuth2 authentication out of the box, optionally with
    scope handling.

        @protected_resource()
        def my_view(request):
            # An access token is required to get here...
            # ...
            pass
    """
    _scopes = scopes or []

    def decorator(view_func):
        @wraps(view_func)
        def _validate(request, *args, **kwargs):
            validator = validator_cls()
            core = OAuthLibCore(server_cls(validator))
            valid, oauthlib_req = core.verify_request(request, scopes=_scopes)
            if valid:
                # here we check if the access to resource is allowed by the token's scope.
                if not allow_resource(oauthlib_req.access_token, request.method, request.path):
                    # Return a 404 on error in order to avoid notifying user of object's existence
                    return JsonResponse({
                                             "error": {
                                                 "code": 404,
                                                 "message": "The resource you requested could not be found.",
                                             }
                                         },
                                         status=404)

                request.resource_owner = oauthlib_req.user
                return view_func(request, *args, **kwargs)
            return JsonResponse({
                                     "error": {
                                         "code": 401,
                                         "message": "The token authentication failed.",
                                     }
                                 },
                                 status=401)
        return _validate
    return decorator
