from oauth2_provider.validators import URIValidator
from oauth2_provider.validators import urlsplit
from oauth2_provider.settings import oauth2_settings
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text


class RedirectURIValidator(URIValidator):
    def __init__(self, allowed_schemes):
        self.allowed_schemes = allowed_schemes

    def __call__(self, value):
        super(RedirectURIValidator, self).__call__(value)
        value = force_text(value)
        if len(value.split('#')) > 1:
            raise ValidationError('Redirect URIs must not contain fragments')
        scheme, netloc, path, query, fragment = urlsplit(value)

        if scheme.lower() not in self.allowed_schemes:
            raise ValidationError('Invalid Redirect URI scheme: %s' % scheme.lower())


def validate_uris(value):
    """
    This validator ensures that `value` contains valid blank-separated URIs"
    """
    v = RedirectURIValidator(oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES)
    for uri in value.split():
        v(uri)
