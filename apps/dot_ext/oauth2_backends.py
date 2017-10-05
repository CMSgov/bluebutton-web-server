from __future__ import absolute_import
from __future__ import unicode_literals
from oauth2_provider.oauth2_backends import OAuthLibCore
import json
from ..fhir.bluebutton.models import Crosswalk
from oauth2_provider.models import AccessToken

__author__ = "Alan Viars"


class OAuthLibSMARTonFHIR(OAuthLibCore):

    def create_token_response(self, request):
        """
        Add items to the access_token response to comply with
        SMART on FHIR Authorization
        http://docs.smarthealthit.org/authorization/
        """
        uri, http_method, body, headers = self._extract_params(request)
        extra_credentials = self._get_extra_credentials(request)

        headers, body, status = self.server.create_token_response(uri, http_method, body,
                                                                  headers, extra_credentials)
        fhir_body = json.loads(body)
        token = AccessToken.objects.get(token=fhir_body["access_token"])
        # print("Token Body", body)
        if Crosswalk.objects.filter(user=token.user).exists():
            fhir_body = json.loads(body)
            cw = Crosswalk.objects.get(user=token.user)
            fhir_body["patient"] = cw.fhir_id
            body = json.dumps(fhir_body)
        uri = headers.get("Location", None)

        return uri, headers, body, status
