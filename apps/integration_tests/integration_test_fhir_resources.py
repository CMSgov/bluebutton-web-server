import json

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from oauth2_provider.models import AccessToken
from rest_framework.test import APIClient
from waffle.testutils import override_switch

from apps.dot_ext.tests.demographic_scopes_test_cases import SCOPES_TO_URL_BASE_PATH
from apps.test import BaseApiTest


class IntegrationTestFhirApiResources(StaticLiveServerTestCase):
    '''
    This sets up a live server in the background to test with.
    For more details, see https://docs.djangoproject.com/en/3.1/topics/testing/tools/#liveservertestcase

    This uses APIClient to test the BB2 FHIR API endpoints with the default (Fred) access token.
    '''
    fixtures = ['scopes.json']

    @override_switch('require-scopes', active=True)
    def test_userinfo_endpoint(self):
        print("---")
        print("--- test_userinfo_endpoint()")
        print("---")

        base_path = SCOPES_TO_URL_BASE_PATH['profile']["base_path"]

        # Setup token in APIClient
        client = APIClient()

        # Perform auth flow here --- when selenium is included later.
        # For now, creating user thru access token using BaseApiTest for now.

        # Setup instance of BaseApiTest
        base_api_test = BaseApiTest()

        # Setup client for BaseApiTest client
        base_api_test.client = client

        # Setup read/write capability for create_token()
        base_api_test.read_capability = base_api_test._create_capability('Read', [])
        base_api_test.write_capability = base_api_test._create_capability('Write', [])

        # create user, app, and access token
        first_name = "John"
        last_name = "Doe"
        access_token = base_api_test.create_token(first_name, last_name)

        # Test scope in access_token
        at = AccessToken.objects.get(token=access_token)

        # Setup Bearer token:
        client.credentials(HTTP_AUTHORIZATION="Bearer " + at.token)

        # Test FHIR endpoint:
        url = self.live_server_url + base_path
        print("---")
        print("---    CALLING:  URL: ", url)
        print("---")
        response = client.get(url)
        content = json.loads(response.content)
        print("---")
        print("---  content: ", content)
        print("---")
        self.assertEqual(response.status_code, 200)

    @override_switch('require-scopes', active=True)
    def test_patient_endpoint(self):
        print("---")
        print("--- test_patient_endpoint()")
        print("---")

        base_path = SCOPES_TO_URL_BASE_PATH['patient/Patient.read']["base_path"]

        # Setup token in APIClient
        client = APIClient()

        # Perform auth flow here --- when selenium is included later.
        # For now, creating user thru access token using BaseApiTest for now.

        # Setup instance of BaseApiTest
        base_api_test = BaseApiTest()

        # Setup client for BaseApiTest client
        base_api_test.client = client

        # Setup read/write capability for create_token()
        base_api_test.read_capability = base_api_test._create_capability('Read', [])
        base_api_test.write_capability = base_api_test._create_capability('Write', [])

        # create user, app, and access token
        first_name = "John"
        last_name = "Doe"
        access_token = base_api_test.create_token(first_name, last_name)

        # Test scope in access_token
        at = AccessToken.objects.get(token=access_token)

        # Setup Bearer token:
        client.credentials(HTTP_AUTHORIZATION="Bearer " + at.token)

        # Test FHIR endpoint:
        url = self.live_server_url + base_path
        print("---")
        print("---    CALLING:  URL: ", url)
        print("---")
        response = client.get(url)
        content = json.loads(response.content)
        print("---")
        print("---  content: ", content)
        print("---")
        self.assertEqual(response.status_code, 200)
