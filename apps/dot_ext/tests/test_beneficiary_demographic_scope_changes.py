import json
from apps.test import BaseApiTest
from django.urls import reverse
from oauth2_provider.compat import parse_qs, urlparse
from oauth2_provider.models import AccessToken
from rest_framework.test import APIClient
from waffle.testutils import override_switch
from ..models import Application


class TestBeneficiaryDemographicScopesChanges(BaseApiTest):
    fixtures = ['scopes.json']

    @override_switch('require-scopes', active=True)
    def _authorize_and_request_token(self, payload, application):
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://example.it',
            'client_id': application.client_id,
        }
        return self.client.post(reverse('oauth2_provider:token'), data=token_request_data)

    def _assertScopeResponse(self, scope, scopes_granted_access_token, response, content):
        # Assert expected response and content for scope vs. what is granted.
        if scope in scopes_granted_access_token:
            # Path is allowed by scopes.
            self.assertEqual(response.status_code, 200)
        else:
            # Path is NOT allowed by scopes.
            self.assertEqual(response.status_code, 403)

    @override_switch('require-scopes', active=True)
    def test_bene_demo_scopes_change(self):
        """
        Test authorization related to different, beneficiary "share_demographic_scopes"
        choices made on subsequent authorizations.

        Test that previous access/refresh tokens are updated related to the
        beneficiary's sharing choice. Tokens should be deleted when the choices is to
        NOT share demographic scopes.
        """
        # create a user
        self._create_user('anna', '123456')

        # create an application and add some extra capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')

        # Give the app some additional scopes.
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        application.scope.add(capability_a, capability_b)

        # user logs in
        self.client.login(username='anna', password='123456')

        # Scopes lists for testing
        APPLICATION_SCOPES_FULL = ['patient/Patient.read', 'profile',
                                   'patient/ExplanationOfBenefit.read', 'patient/Coverage.read',
                                   'capability-a', 'capability-b']
        APPLICATION_SCOPES_NON_DEMOGRAPHIC = ['patient/ExplanationOfBenefit.read',
                                              'patient/Coverage.read', 'capability-a', 'capability-b']

        # Setup request parameters for test case
        request_scopes = APPLICATION_SCOPES_FULL

        # Init API client for request calls
        client = APIClient()

        payload = {'client_id': application.client_id,
                   'response_type': 'code',
                   'redirect_uri': 'http://example.it',
                   'expires_in': 86400,
                   'allow': True}

        request_scopes = APPLICATION_SCOPES_FULL
        # Scopes to be requested in the authorization request
        payload['scope'] = ' '.join(request_scopes)

        # ------ TEST #1: 1st authorization: Beneficary authorizes to share demographic data. ------
        payload['share_demographic_scopes'] = True

        # Perform authorization request
        response = self._authorize_and_request_token(payload, application)

        # Assert auth request was successful
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))

        # Test scope in response content
        self.assertEqual(sorted(content['scope'].split()), sorted(APPLICATION_SCOPES_FULL))

        # Test scope in access_token
        token_1 = AccessToken.objects.get(token=content['access_token'])
        refresh_token_1 = content['refresh_token']

        scopes_granted_access_token = sorted(token_1.scope.split())
        self.assertEqual(scopes_granted_access_token, sorted(APPLICATION_SCOPES_FULL))

        # Setup token_1 in APIClient
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token_1.token)

        # Test access to userinfo end point?
        response = client.get("/v1/connect/userinfo")
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        # ------ TEST #2: SAME authorization: Beneficary authorizes to share FULL demographic data. ------
        payload['share_demographic_scopes'] = True

        # Perform authorization request
        response = self._authorize_and_request_token(payload, application)

        # Assert auth request was successful
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))

        # Test scope in response content
        self.assertEqual(sorted(content['scope'].split()), sorted(APPLICATION_SCOPES_FULL))

        # Test scope in access_token
        token_2 = AccessToken.objects.get(token=content['access_token'])

        scopes_granted_access_token = sorted(token_2.scope.split())
        self.assertEqual(scopes_granted_access_token, sorted(APPLICATION_SCOPES_FULL))

        # Setup token_2 in APIClient
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token_2.token)

        # Test access to userinfo end point?
        response = client.get("/v1/connect/userinfo")
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        # ------ TEST #3:  3nd authorization: Beneficary authorizes NOT to share demographic data. ------
        payload['share_demographic_scopes'] = False

        # Perform authorization request
        response = self._authorize_and_request_token(payload, application)

        # Assert auth request was successful
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))

        # Test scope in response content
        self.assertEqual(sorted(content['scope'].split()), sorted(APPLICATION_SCOPES_NON_DEMOGRAPHIC))

        # Test scope in access_token
        token_3 = AccessToken.objects.get(token=content['access_token'])
        scopes_granted_access_token = sorted(token_3.scope.split())
        self.assertEqual(scopes_granted_access_token, sorted(APPLICATION_SCOPES_NON_DEMOGRAPHIC))

        # Setup token_3 in APIClient
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token_3.token)

        # Test access to userinfo end point? NO PERMISSION!
        response = client.get("/v1/connect/userinfo")
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(content.get('detail', None), "You do not have permission to perform this action.")

        # ------ TEST #4:  Test token_1 from TEST #1 access to userinfo? Does it still have access? ------
        # Setup token in APIClient
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token_1.token)

        # Test access to userinfo end point? NO ACCESS!
        response = client.get("/v1/connect/userinfo")
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(content.get('detail', None), "Authentication credentials were not provided.")

        # ------ TEST #5:  Test token_1 from TEST #1 token refresh? NO ACCESS!
        refresh_request_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token_1,
            'redirect_uri': 'http://example.it',
            'client_id': application.client_id,
            'client_secret': application.client_secret,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=refresh_request_data)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(content.get('error', None), "invalid_grant")

        # ------ TEST #6: Beneficary authorizes to share FULL demographic data again.. ------
        payload['share_demographic_scopes'] = True

        # Perform authorization request
        response = self._authorize_and_request_token(payload, application)

        # Assert auth request was successful
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))

        # Test scope in response content
        self.assertEqual(sorted(content['scope'].split()), sorted(APPLICATION_SCOPES_FULL))

        # Test scope in access_token
        token_6 = AccessToken.objects.get(token=content['access_token'])

        scopes_granted_access_token = sorted(token_6.scope.split())
        self.assertEqual(scopes_granted_access_token, sorted(APPLICATION_SCOPES_FULL))

        # Setup token_6 in APIClient
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token_6.token)

        # Test access to userinfo end point?
        response = client.get("/v1/connect/userinfo")
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        # ------ TEST #7: Test token_3 from TEST #3 again. It should still have access, but no permission with status=403.

        # Setup token_3 in APIClient from previous step.
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token_3.token)

        # Test access to userinfo end point?
        response = client.get("/v1/connect/userinfo")
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(content.get('detail', None), "You do not have permission to perform this action.")
