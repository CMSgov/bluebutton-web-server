from oauth2_provider.compat import parse_qs, urlparse
from django.core.urlresolvers import reverse

from apps.test import BaseApiTest
from ..models import Application


class TestAuthorizeWithCustomScheme(BaseApiTest):
    def test_post_with_valid_non_standard_scheme(self):
        redirect_uri = 'com.custom.bluebutton://example.it'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        self.client.login(username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)

        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 200)

    def test_post_with_invalid_non_standard_scheme(self):
        redirect_uri = 'com.custom.bluebutton://example.it'
        bad_redirect_uri = 'com.custom.bad://example.it'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        self.client.login(username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': bad_redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)

        self.assertEqual(response.status_code, 400)
