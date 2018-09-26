import base64
import hashlib
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

from oauth2_provider.models import get_grant_model

from django.core.exceptions import ObjectDoesNotExist

Grant = get_grant_model()


class PKCEServerMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_types['code'].default_auth_grant.custom_validators.post_auth.append(validate_code_challenge_method)
        self.response_types['code'].default_auth_grant.custom_validators.post_token.append(validate_code_verifier)


def validate_code_challenge_method(request):
    if hasattr(request, 'code_challenge_method') and request.code_challenge_method:
        if request.code_challenge_method != "S256":
            raise OAuth2Error("S256 code challenge method required for pkce")

    elif hasattr(request, 'code_challenge') and request.code_challenge:
        raise OAuth2Error("S256 code challenge method required for pkce")
    return {}


def validate_code_verifier(request):
    grant = Grant.objects.get(code=request.code, application=request.client)
    # try :
    # except django.db.models.fields.related_descriptors.RelatedObjectDoesNotExist
    try:
        grant.codechallenge
    except ObjectDoesNotExist:
        return {}
    # Perform transform
    # we only allow sha256 code challenge methods
    try:
        code_verifier = request.code_verifier
    except AttributeError:
        raise OAuth2Error("code_verifier required for this request")

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('ASCII')).digest()).decode('utf-8')

    if code_challenge != grant.codechallenge.challenge:
        raise OAuth2Error("code_challenge does not match")

    # check grant.code against request.code
    return {}
