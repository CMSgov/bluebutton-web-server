from oauth2_provider.validators import URIValidator
from oauth2_provider.validators import urlsplit
from oauth2_provider.settings import oauth2_settings
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from os import path as ospath


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
            raise ValidationError('Invalid Redirect URI scheme: %s, Must be one of %s' % (scheme.lower(), self.allowed_schemes))


def validate_uris(value):
    """
    This validator ensures that `value` contains valid blank-separated URIs"
    """
    v = RedirectURIValidator(oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES)
    for uri in value.split():
        v(uri)


# Validate that there are no HTML tags
def validate_notags(value):
    if value != strip_tags(value):
        raise ValidationError(_('The text contains HTML tags. Please use plain-text only!'))


# Validate the applciation logo imagefield in form clean
def validate_logo_image(value):
    file_extension = ospath.splitext(value.name)[1]
    if not file_extension.lower() in ['.jpg']:
        raise ValidationError("The file type must be JPEG with a .jpg file extension!")

    if value.size > int(settings.APP_LOGO_SIZE_MAX) * 1024:
        raise ValidationError("Max file size is %sKB. Your file size is %0.1fKB"
                              % (str(settings.APP_LOGO_SIZE_MAX), value.size / 1024))

    if value.image.width > int(settings.APP_LOGO_WIDTH_MAX):
        raise ValidationError("Max image width is %s. Your image width is %s."
                              % (str(settings.APP_LOGO_WIDTH_MAX), str(value.image.width)))

    if value.image.height > int(settings.APP_LOGO_HEIGHT_MAX):
        raise ValidationError("Max image height is %s. Your image height is %s."
                              % (str(settings.APP_LOGO_HEIGHT_MAX), str(value.image.height)))
