from __future__ import absolute_import
from __future__ import unicode_literals

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text
from django.utils import timezone
from django.utils.timezone import timedelta

from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.oauth2_validators import OAuth2Validator

from oauth2_provider.validators import URIValidator
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.validators import urlsplit


class SingleAccessTokenValidator(OAuth2Validator):
    """
    This custom oauth2 validator checks if a valid token
    exists for the current user/application and return
    it instead of creating a new one.
    """

    def save_bearer_token(self, token, request, *args, **kwargs):
        """
        Check if an access_token exists for the couple user/application
        that is valid and authorized for the same scopes and ensures that
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


class RedirectURIValidator(URIValidator):
    def __init__(self, allowed_schemes):
        self.allowed_schemes = allowed_schemes

    def __call__(self, value):
        super(RedirectURIValidator, self).__call__(value)
        value = force_text(value)
        if len(value.split('#')) > 1:
            raise ValidationError('Redirect URIs must not contain fragments')
        scheme, netloc, path, query, fragment = urlsplit(value)

        # Fix the mobile endpoint validation
        # Allow 2 character alpha plus 8 numerics
        if scheme.lower() in self.allowed_schemes:
            pass

        elif scheme.lower() not in self.allowed_schemes:
            raise ValidationError('Invalid Redirect URI:[%s]' % scheme.lower())


def validate_uris(value):
    """
    This validator ensures that `value` contains valid blank-separated URIs"
    """
    v = RedirectURIValidator(oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES)
    for uri in value.split():
        regex = set_regex()
        if compare_to_regex(regex, uri):
            pass
        else:
            v(uri)


def set_regex():
    """
    Set the regex value
    :return:
    """
    regex = getattr(settings,
                    'OAUTH2_MOBILE_REDIRECT_REGEX',
                    r'\b[a-zA-Z]{2}[0-9]{8}\b')

    return regex


def compare_to_regex(regex, uri):
    """

    :param regex:
    :param uri:
    :return:
    """
    if re.findall(regex, uri):
        return True
    else:
        return False
