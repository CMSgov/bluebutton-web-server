import json
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from oauth2_provider.oauth2_backends import OAuthLibCore
from oauth2_provider.models import AccessToken, RefreshToken
from ..fhir.bluebutton.models import Crosswalk
from .loggers import update_session_auth_flow_trace_from_code


class OAuthLibSMARTonFHIR(OAuthLibCore):

    def create_token_response(self, request):
        """
        Add items to the access_token response to comply with
        SMART on FHIR Authorization
        http://docs.smarthealthit.org/authorization/
        """
        # Get session values previously stored in AuthFlowUuid from AuthorizationView.form_valid() from code.
        body = dict(self.extract_body(request))
        code = body.get('code', None)
        update_session_auth_flow_trace_from_code(request, code)

        uri, headers, body, status = super(OAuthLibSMARTonFHIR, self).create_token_response(request)

        # cribed from
        # https://github.com/evonove/django-oauth-toolkit/blob/2cd1f0dccadb8e74919a059d9b4985f9ecb1d59f/oauth2_provider/views/base.py#L192
        if status == 200:
            fhir_body = json.loads(body)
            token = AccessToken.objects.get(token=fhir_body.get("access_token"))

            if Crosswalk.objects.filter(user=token.user).exists():
                fhir_body = json.loads(body)
                cw = Crosswalk.objects.get(user=token.user)
                fhir_body["patient"] = cw.fhir_id
                body = json.dumps(fhir_body)

            # When BENE chooses NOT to share demographic scopes, clean up previous access/refresh tokens.
            app = token.application
            user = token.user
            scope = token.scope

            # Does new token scope NOT contain BENE_PERSONAL_INFO_SCOPES?
            if not set(settings.BENE_PERSONAL_INFO_SCOPES).issubset(scope.split()):
                with transaction.atomic():
                    AccessToken.objects.filter(application=app, user=user).filter(~Q(id=token.id)).delete()
                    RefreshToken.objects.filter(application=app, user=user).filter(~Q(access_token=token)).delete()

        return uri, headers, body, status
