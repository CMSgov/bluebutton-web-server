import logging
import requests
from django.conf import settings
from .signals import response_hook

logger = logging.getLogger('hhs_server.%s' % __name__)


class OAuth2Config():
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

    def exchange(self, code):
        logger.debug("token_endpoint %s" % (self.token_endpoint))
        logger.debug("redirect_uri %s" % (self.redirect_uri))

        token_dict = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        response = requests.post(self.token_endpoint,
                                 auth=self.basic_auth(),
                                 json=token_dict,
                                 verify=self.verify_ssl,
                                 hooks={'response': response_hook})

        response.raise_for_status()

        token_response = response.json()
        self.token = token_response
        return self.token['access_token']

    def auth_header(self):
        return {"Authorization": "Bearer %s" % (self.token['access_token'])}
