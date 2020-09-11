import logging
import requests
import datetime

from django.conf import settings
from .signals import response_hook_wrapper
from apps.logging.serializers import SLSTokenResponse

logger = logging.getLogger('hhs_server.%s' % __name__)


class OAuth2Config(object):
    token_endpoint = settings.SLS_TOKEN_ENDPOINT
    redirect_uri = settings.MEDICARE_REDIRECT_URI
    verify_ssl = getattr(settings, 'SLS_VERIFY_SSL', False)
    token = None

    @property
    def client_id(self):
        return getattr(settings, 'SLS_CLIENT_ID', False)

    @property
    def client_secret(self):
        return getattr(settings, 'SLS_CLIENT_SECRET', False)

    def basic_auth(self):
        if self.client_id and self.client_secret:
            return (self.client_id, self.client_secret)
        return None

    def exchange(self, code, request):
        logger.debug("token_endpoint %s" % (self.token_endpoint))
        logger.debug("redirect_uri %s" % (self.redirect_uri))

        token_dict = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        # keep using deprecated conv - no conflict issue
        headers = {"X-SLS-starttime": str(datetime.datetime.utcnow())}
        auth_uuid, application, organization = None, None, None
        application_id, organization_id = None, None
        if request is not None:
            auth_uuid = request.session.get('auth_uuid', None)
            application = request.session.get('application', None)
            application_id = request.session.get('application_id', None)
            organization = request.session.get('organization', None)
            organization_id = request.session.get('organization_id', None)
            headers.update({"X-Request-ID": str(getattr(request, '_logging_uuid', None)
                            if hasattr(request, '_logging_uuid') else '')})
                            
        response = requests.post(
            self.token_endpoint,
            auth=self.basic_auth(),
            json=token_dict,
            headers=headers,
            verify=self.verify_ssl,
            hooks={
                'response': [
                    response_hook_wrapper(sender=SLSTokenResponse,
                                          auth_uuid=auth_uuid,
                                          application=application,
                                          application_id=application_id,
                                          organization=organization,
                                          organization_id=organization_id)]})

        response.raise_for_status()

        token_response = response.json()
        self.token = token_response
        return self.token['access_token']

    def auth_header(self):
        return {"Authorization": "Bearer %s" % (self.token['access_token'])}
