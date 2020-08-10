import json
from oauth2_provider.oauth2_backends import OAuthLibCore
from oauth2_provider.models import AccessToken
from apps.dot_ext.models import AuthFlowUuid
from ..fhir.bluebutton.models import Crosswalk


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
        if code:
            try:
                # Get value previously stored in AuthorizationView.form_valid()
                auth_flow_uuid = AuthFlowUuid.objects.get(code=code)
                auth_uuid = str(auth_flow_uuid.auth_uuid)

                # Delete the no longer needed instance
                auth_flow_uuid.delete()
            except AuthFlowUuid.DoesNotExist:
                auth_uuid = None
        else:
            auth_uuid = None

        # Add value to session for use in apps.logging.signals.handle_token_created()
        if auth_uuid:
            request.session['auth_uuid'] = auth_uuid

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
