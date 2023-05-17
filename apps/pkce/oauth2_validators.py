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

        challenge = request.code_challenge if hasattr(request, 'code_challenge') and request.code_challenge else ""
        # this is needed to match the challenge verification logic in oauth provider
        challenge = challenge.rstrip('=')
        challenge_method = getattr(request, 'code_challenge_method', "")

        g = Grant(
            application=request.client,
            user=request.user,
            code=code["code"],
            expires=expires,
            redirect_uri=request.redirect_uri,
            scope=" ".join(request.scopes),
            code_challenge=challenge,
            code_challenge_method=challenge_method if challenge_method is not None else "",
        )

        # may be demarcated in atomic?
        g.save()

        if challenge and challenge_method:
            CodeChallenge.objects.create(
                grant=g,
                challenge=challenge,
                challenge_method=challenge_method,
            )
