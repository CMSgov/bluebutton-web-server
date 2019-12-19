from django.utils import timezone
from django.utils.timezone import timedelta

from oauth2_provider.models import get_grant_model
from oauth2_provider.settings import oauth2_settings
from .models import CodeChallenge

Grant = get_grant_model()


class PKCEValidatorMixin(object):

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        expires = timezone.now() + timedelta(
            seconds=oauth2_settings.AUTHORIZATION_CODE_EXPIRE_SECONDS)
        g = Grant(
            application=request.client,
            user=request.user,
            code=code["code"],
            expires=expires,
            redirect_uri=request.redirect_uri,
            scope=" ".join(request.scopes),
        )
        g.save()
        if hasattr(request, 'code_challenge') and request.code_challenge:
            CodeChallenge.objects.create(
                grant=g,
                challenge=request.code_challenge,
                challenge_method=getattr(request, 'code_challenge_method', None),
            )
