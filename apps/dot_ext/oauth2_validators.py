from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils import timezone
from django.utils.timezone import timedelta

from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.oauth2_validators import OAuth2Validator


class SingleAccessTokenValidator(OAuth2Validator):
    """
    This custom oauth2 validator checks if a valid token
    exists for the current user/application and return
    it instead of creating a new one.
    """

    def save_bearer_token(self, token, request, *args, **kwargs):
        """
        Check if an access_token exists for the couple user/application
        that is valid and authorized for the same scopes and esures that
        no refresh token was used.

        If all the conditions are true the same access_token is issued.
        Otherwise a new one is created with the default strategy.
        """
        # this queryset identifies all the valid access tokens
        # for the couple user/application.
        previous_valid_tokens = AccessToken.objects.filter(
            user=request.user, application=request.client,
        ).filter(expires__gt=timezone.now()).order_by('-expires')

        # if a refresh token was not used and a valid token exists we
        # can replace the new generated token with the old one.
        if not request.refresh_token and previous_valid_tokens.exists():
            for access_token in previous_valid_tokens:
                # the previous access_token must allow access to the same scope
                # or bigger
                if access_token.allow_scopes(token['scope'].split()):
                    token['access_token'] = access_token.token
                    expires_in = access_token.expires - timezone.now()
                    token['expires_in'] = expires_in.total_seconds()

                    if hasattr(access_token, 'refresh_token'):
                        token['refresh_token'] = access_token.refresh_token.token

                    # break the loop and exist because we found to old token
                    return

        # default behaviour when no old token is found
        if request.refresh_token:
            # remove used refresh token
            try:
                RefreshToken.objects.get(token=request.refresh_token).revoke()
            except RefreshToken.DoesNotExist:
                assert()  # TODO though being here would be very strange, at least log the error

        expires = timezone.now() + timedelta(seconds=token['expires_in'])
        if request.grant_type == 'client_credentials':
            request.user = None

        access_token = AccessToken(
            user=request.user,
            scope=token['scope'],
            expires=expires,
            token=token['access_token'],
            application=request.client)
        access_token.save()

        if 'refresh_token' in token:
            refresh_token = RefreshToken(
                user=request.user,
                token=token['refresh_token'],
                application=request.client,
                access_token=access_token
            )
            refresh_token.save()
