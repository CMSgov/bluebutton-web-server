from oauth2_provider.contrib.rest_framework import authentication
from django.utils import timezone
from rest_framework import exceptions


class OAuth2ResourceOwner(authentication.OAuth2Authentication):
    def authenticate(self, request):
        user_auth_tuple = super(OAuth2ResourceOwner, self).authenticate(request)
        access_token_query_param = request.GET.get("access_token", None)
        if access_token_query_param is not None:
            raise exceptions.ParseError(
                "Using the access token in the query parameters is not supported. "
                "Use the Authorization header instead"
            )

        # fix until https://github.com/jazzband/django-oauth-toolkit/commit/f86dfb8a7f20065850fe3b3629e18723658f835d is stable
        if not hasattr(request, "oauth2_error"):
            request.oauth2_error = {}

        if user_auth_tuple is not None:
            user, access_token = user_auth_tuple
            request.resource_owner = user
            if not hasattr(user, "crosswalk"):
                return None
            request.crosswalk = user.crosswalk

            # Update Application activity metric datetime fields
            access_token.application.last_active = timezone.now()
            if access_token.application.first_active is None:
                access_token.application.first_active = (
                    access_token.application.last_active
                )
            # BB2-2008 call dedicated save on application model to avoid
            # unnecessary validations
            access_token.application.save_without_validate()

            return user, access_token
        return None
