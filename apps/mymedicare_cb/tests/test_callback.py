import requests
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from urllib.parse import urlparse, parse_qs
from apps.mymedicare_cb.views import generate_nonce
from apps.mymedicare_cb.models import AnonUserState
from apps.mymedicare_cb.authorization import OAuth2Config
from httmock import urlmatch, all_requests, HTTMock
from django.contrib.auth.models import Group
from apps.fhir.server.models import ResourceRouter

from .responses import patient_response


class MyMedicareBlueButtonClientApiUserInfoTest(TestCase):
    """
    Tests for the MyMedicare login and SLS Callback
    """

    def setUp(self):
        self.callback_url = reverse('mymedicare-sls-callback')
        self.login_url = reverse('mymedicare-login')
        Group.objects.create(name='BlueButton')
        ResourceRouter.objects.create(pk=settings.FHIR_SERVER_DEFAULT, fhir_url="http://bogus.com/")

    def test_login_url_success(self):
        """
        Test well-formed login_url has expected content
        """
        fake_login_url = 'https://example.com/login?scope=openid'

        with self.settings(ALLOW_CHOOSE_LOGIN=False, MEDICARE_LOGIN_URI=fake_login_url, MEDICARE_REDIRECT_URI='/123'):
            response = self.client.get(self.login_url + '?next=/')
            self.assertEqual(response.status_code, 302)
            query = parse_qs(urlparse(response['Location']).query)
            path = response['Location'].split('?')[0]
            self.assertEqual(path, 'https://example.com/login')
            self.assertEqual(query['redirect_uri'][0], '/123')

    def test_callback_url_missing_state(self):
        """
        Test callback_url returns HTTP 400 when
        necessary GET parameter state is missing.
        """
        response = self.client.get(self.callback_url)
        self.assertEqual(response.status_code, 400)

    def test_callback_url_success(self):
        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(state=state, next_uri="http://www.google.com")
        # mock sls token endpoint

        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/token')
        def sls_token_mock(url, request):
            return {
                'status_code': 200,
                'content': {'access_token': 'works'},
            }

        # mock sls user info endpoint
        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/userinfo')
        def sls_user_info_mock(url, request):
            return {
                'status_code': 200,
                'content': {
                    'sub': '0123456789abcdefghijklmnopqrstuvwxyz',
                    'given_name': '',
                    'family_name': '',
                    'email': 'bob@bobserver.bob',
                },
            }

        # mock fhir user info endpoint
        @urlmatch(netloc='bogus.com', path='/Patient/')
        def fhir_patient_info_mock(url, request):
            return {
                'status_code': 200,
                'content': patient_response,
            }

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        with HTTMock(sls_token_mock,
                     sls_user_info_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})
            # assert http redirect
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, "http://www.google.com", fetch_redirect_response=False)
            # assert login
            self.assertIn('_auth_user_id', self.client.session)

    def test_callback_url_failure(self):
        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(state=state, next_uri="http://www.google.com")

        @all_requests
        def catchall(url, request):
            return {
                'status_code': 403,
                'content': {'error': 'nope'},
            }

        with HTTMock(catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})
            # assert http redirect
            self.assertEqual(response.status_code, 502)

    def test_sls_token_exchange_w_creds(self):
        with self.settings(SLS_CLIENT_ID="test",
                           SLS_CLIENT_SECRET="stest"):

            sls_client = OAuth2Config()

            @all_requests
            def catchall(url, request):
                sls_auth_header = request.headers['Authorization']
                self.assertEqual(sls_auth_header, 'Basic dGVzdDpzdGVzdA==')
                return {
                    'status_code': 200,
                    'content': {
                        'access_token': 'test_tkn',
                    },
                }

            with HTTMock(catchall):
                tkn = sls_client.exchange("test_code")
                self.assertEquals(tkn, "test_tkn")

    def test_failed_sls_token_exchange(self):
        with self.settings(SLS_CLIENT_ID="test",
                           SLS_CLIENT_SECRET="stest"):

            sls_client = OAuth2Config()

            @all_requests
            def catchall(url, request):
                sls_auth_header = request.headers['Authorization']
                self.assertEqual(sls_auth_header, 'Basic dGVzdDpzdGVzdA==')
                return {
                    'status_code': 401,
                    'content': {
                        'error': 'nope!',
                    },
                }

            with HTTMock(catchall):
                with self.assertRaises(requests.exceptions.HTTPError):
                    tkn = sls_client.exchange("test_code")
                    self.assertEquals(tkn, "test_tkn")
