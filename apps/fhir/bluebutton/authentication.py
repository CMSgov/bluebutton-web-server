from oauth2_provider.contrib.rest_framework import authentication


class OAuth2ResourceOwner(authentication.OAuth2Authentication):
    def authenticate(self, request):
        user_auth_tuple = super(OAuth2ResourceOwner, self).authenticate(request)
        if user_auth_tuple is not None:
            user, access_token = user_auth_tuple
            request.resource_owner = user
            return user, access_token
        return None
