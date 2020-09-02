import json
from oauth2_provider.oauth2_backends import OAuthLibCore
from oauth2_provider.models import AccessToken
from ..fhir.bluebutton.models import Crosswalk
from .loggers import update_session_auth_flow_trace


class OAuthLibSMARTonFHIR(OAuthLibCore):

    def create_token_response(self, request):
        """
        Add items to the access_token response to comply with
        SMART on FHIR Authorization
        http://docs.smarthealthit.org/authorization/
        """
        # Get auth_uuid from authorization flow AuthFlowUuid instance for logging
        body = dict(self.extract_body(request))
        code = body.get('code', None)

        # Get value previously stored in AuthorizationView.form_valid()
        update_session_auth_flow_trace(request=request, code=code)

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

        return uri, headers, body, status
