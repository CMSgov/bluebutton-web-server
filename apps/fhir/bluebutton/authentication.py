from oauth2_provider.contrib.rest_framework import authentication
from django.utils import timezone


class OAuth2ResourceOwner(authentication.OAuth2Authentication):
    def authenticate(self, request):
        user_auth_tuple = super(OAuth2ResourceOwner, self).authenticate(request)

        # fix until https://github.com/jazzband/django-oauth-toolkit/commit/f86dfb8a7f20065850fe3b3629e18723658f835d is stable
        if not hasattr(request, 'oauth2_error'):
            request.oauth2_error = {}

        if user_auth_tuple is not None:
            user, access_token = user_auth_tuple
            request.resource_owner = user
            if not hasattr(user, 'crosswalk'):
                return None
            request.crosswalk = user.crosswalk

            # Update Application activity metric datetime fields
            access_token.application.last_active = timezone.now()
            if access_token.application.first_active is None:
                access_token.application.first_active = access_token.application.last_active
            access_token.application.save()

            return user, access_token
        return None
