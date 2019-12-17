import logging
import requests
from django.conf import settings
from .signals import response_hook

logger = logging.getLogger('hhs_server.%s' % __name__)


class OAuth2Config(object):
    token_endpoint = settings.SLS_TOKEN_ENDPOINT
    redirect_uri = settings.MEDICARE_REDIRECT_URI
    # IR TODO - we should require SSL verification, at least in prod, rather than defaulting to False
    verify_ssl = getattr(settings, 'SLS_VERIFY_SSL', False)
    token = None

    @property
    def client_id(self):
        # TODO why is this defaulting to False? I'd expect this to default to nil, unless this is a python/django convention?
        return getattr(settings, 'SLS_CLIENT_ID', False)

    @property
    def client_secret(self):
        # TODO why is this defaulting to False? Ditto above
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

        # IR TODO - make sure this is being logged. It looks like it is in views.py:42-44 but should doublecheck
        response.raise_for_status()

        token_response = response.json()
        self.token = token_response
        # IR TODO - can we validate the token itself?
        return self.token['access_token']

    def auth_header(self):
        return {"Authorization": "Bearer %s" % (self.token['access_token'])}
