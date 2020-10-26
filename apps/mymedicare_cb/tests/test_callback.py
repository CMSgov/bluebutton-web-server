import json
import requests
import uuid

from datetime import datetime
from django.contrib.auth.models import Group, User
from django.utils.dateparse import parse_duration
from django.utils.text import slugify
from django.urls import reverse
from django.test import TestCase
from httmock import urlmatch, all_requests, HTTMock
from urllib.parse import urlparse, parse_qs

from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.models import Approval, Application
from apps.fhir.bluebutton.models import Crosswalk
from apps.mymedicare_cb.authorization import OAuth2Config
from apps.mymedicare_cb.models import AnonUserState
from apps.mymedicare_cb.views import generate_nonce
from .responses import patient_response


class MyMedicareBlueButtonClientApiUserInfoTest(TestCase):
    """
    Tests for the MyMedicare login and SLS Callback
    """

    def setUp(self):
        self.callback_url = reverse('mymedicare-sls-callback')
        self.login_url = reverse('mymedicare-login')
        Group.objects.create(name='BlueButton')

    def test_login_url_success(self):
        """
        Test well-formed login_url has expected content
        """
        fake_login_url = 'https://example.com/login?scope=openid'

        with self.settings(MEDICARE_LOGIN_URI=fake_login_url, MEDICARE_REDIRECT_URI='/123'):
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

    def test_authorize_uuid_dne(self):
        auth_uri = reverse(
            'oauth2_provider:authorize-instance',
            args=[uuid.uuid4()])
        response = self.client.get(auth_uri)
        self.assertEqual(302, response.status_code)

    def _create_capability(self, name, urls, group=None, default=True):
        """
        Helper method that creates a ProtectedCapability instance
        that controls the access for the set of `urls`.
        """
        group = group or self._create_group('test')
        capability = ProtectedCapability.objects.create(
            default=default,
            title=name,
            slug=slugify(name),
            protected_resources=json.dumps(urls),
            group=group)
        return capability

    def _create_group(self, name):
        """
        Helper method that creates a group instance
        with `name`.
        """
        group, _ = Group.objects.get_or_create(name=name)
        return group

    def test_authorize_uuid(self):
        user = User.objects.create_user(
            "bob",
            password="bad")
        Crosswalk.objects.create(
            user=user,
            fhir_id="-20000000002346",
            user_hicn_hash="96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7",
            user_mbi_hash="98765432137efea543f4f370f96f1dbf01c3e3129041dba3ea43675987654321")
        application = Application.objects.create(
            redirect_uris="http://test.com",
            authorization_grant_type='authorization-code',
            name="test01",
            user=user)

        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        application.scope.add(capability_a, capability_b)

        approval = Approval.objects.create(
            user=user)
        auth_uri = reverse(
            'oauth2_provider:authorize-instance',
            args=[approval.uuid])
        response = self.client.get(auth_uri, data={
            "client_id": application.client_id,
            "redirect_uri": "http://test.com",
            "response_type": "code"})
        self.assertEqual(200, response.status_code)
        approval.refresh_from_db()
        self.assertEqual(application, approval.application)
        self.assertNotIn('_auth_user_id', self.client.session)
        response = self.client.post(auth_uri, data={
            "client_id": "bad",
            "redirect_uri": "http://test.com",
            "response_type": "code"})
        self.assertEqual(302, response.status_code)
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://test.com',
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(auth_uri, data=payload)
        self.assertEqual(302, response.status_code)
        self.assertIn("code=", response.url)
        approval.created_at = datetime.now() - parse_duration("601")
        approval.save()
        response = self.client.post(auth_uri, data={
            "client_id": application.client_id,
            "redirect_uri": "http://test.com",
            "response_type": "code"})
        self.assertEqual(302, response.status_code)

    def test_callback_url_success(self):
        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri="http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test")
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
                    'sub': '00112233-4455-6677-8899-aabbccddeeff',
                    'given_name': '',
                    'family_name': '',
                    'email': 'bob@bobserver.bob',
                    'hicn': '1234567890A',
                    'mbi': '1SA0A00AA00',
                },
            }

        # mock fhir user info endpoint
        @urlmatch(netloc='fhir.backend.bluebutton.hhsdevcloud.us', path='/v1/fhir/Patient/')
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
            # need to fake an auth flow context to pass
            # validation of Request.prepare(...) in
            # apps.fhir.server.authentication.py->search_fhir_id_by_identifier(...)
            s = self.client.session
            s.update({"auth_uuid": "84b4afdc-d85d-4ea4-b44c-7bde77634429",
                      "auth_app_id": "2",
                      "auth_app_name": "TestApp-001",
                      "auth_client_id": "uouIr1mnblrv3z0PJHgmeHiYQmGVgmk5DZPDNfop"})
            s.save()
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})
            # assert http redirect
            self.assertEqual(response.status_code, 302)
            self.assertIn("client_id=test", response.url)
            self.assertIn("redirect_uri=test.com", response.url)
            # self.assertRedirects(response, "http://www.google.com", fetch_redirect_response=False)
            # assert login
            self.assertNotIn('_auth_user_id', self.client.session)

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
                tkn = sls_client.exchange("test_code", None)
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
                    tkn = sls_client.exchange("test_code", None)
                    self.assertEquals(tkn, "test_tkn")

    def test_callback_exceptions(self):
        # BB2-237: Added to test ASSERTS replaced with exceptions.
        #          These are typically for conditions that should never be reached, so generate a 500.
        ERROR_MSG_MYMEDICARE = "An error occurred connecting to account.mymedicare.gov"

        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri="http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test")

        # mock sls token endpoint
        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/token')
        def sls_token_mock(url, request):
            return {
                'status_code': 200,
                'content': {'access_token': 'works'},
            }

        # mock sls token endpoint with http error
        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/token')
        def sls_token_http_error_mock(url, request):
            raise requests.exceptions.HTTPError

        # mock sls user info endpoint
        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/userinfo')
        def sls_user_info_mock(url, request):
            return {
                'status_code': 200,
                'content': {
                    'sub': '00112233-4455-6677-8899-aabbccddeeff',
                    'hicn': '1234567890A',
                    'mbi': '1SA0A00AA00',
                },
            }

        # mock sls user info endpoint with http error
        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/userinfo')
        def sls_user_info_http_error_mock(url, request):
            raise requests.exceptions.HTTPError

        # mock sls user info endpoint with out a sub/username
        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/userinfo')
        def sls_user_info_no_sub_mock(url, request):
            return {
                'status_code': 200,
                'content': {
                    'hicn': '1234567890A',
                    'mbi': '1SA0A00AA00',
                },
            }

        # mock sls user info endpoint with empty hicn
        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/userinfo')
        def sls_user_info_empty_hicn_mock(url, request):
            return {
                'status_code': 200,
                'content': {
                    'sub': '00112233-4455-6677-8899-aabbccddeeff',
                    'hicn': '',
                    'mbi': '1SA0A00AA00',
                },
            }

        # mock sls user info endpoint
        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/userinfo')
        def sls_user_info_invalid_mbi_mock(url, request):
            return {
                'status_code': 200,
                'content': {
                    'sub': '00112233-4455-6677-8899-aabbccddeeff',
                    'hicn': '1234567890A',
                    'mbi': '1SA0A00SS00',
                },
            }

        # mock fhir user info endpoint
        @urlmatch(netloc='fhir.backend.bluebutton.hhsdevcloud.us', path='/v1/fhir/Patient/')
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

        # Change existing hash prior to test
        cw = Crosswalk.objects.get(id=1)
        saved_hicn_hash = cw._user_id_hash
        saved_mbi_hash = cw._user_mbi_hash
        saved_fhir_id = cw.fhir_id
        cw._user_id_hash = "XXX"
        cw.save()

        with HTTMock(sls_token_mock,
                     sls_user_info_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})

            # assert 500 exception
            self.assertEqual(response.status_code, 500)
            content = json.loads(response.content)
            self.assertEqual(content['error'], "Found user's hicn did not match")

        # Restore hicn hash and change existing mbi hash prior to next test
        cw = Crosswalk.objects.get(id=1)
        cw._user_id_hash = saved_hicn_hash
        cw._user_mbi_hash = "XXX"
        cw.save()

        with HTTMock(sls_token_mock,
                     sls_user_info_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})

            # assert 500 exception
            self.assertEqual(response.status_code, 500)
            content = json.loads(response.content)
            self.assertEqual(content['error'], "Found user's mbi did not match")

        # Restore mbi hash and change existing fhir_id prior to next test
        cw = Crosswalk.objects.get(id=1)
        cw._user_mbi_hash = saved_mbi_hash
        cw._fhir_id = "XXX"
        cw.save()

        with HTTMock(sls_token_mock,
                     sls_user_info_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})

            # assert 500 exception
            self.assertEqual(response.status_code, 500)
            content = json.loads(response.content)
            self.assertEqual(content['error'], "Found user's fhir_id did not match")

        # Restore fhir_id
        cw = Crosswalk.objects.get(id=1)
        cw._fhir_id = saved_fhir_id
        cw.save()

        # With HTTMock sls_user_info_no_sub_mock that has no sub/username
        with HTTMock(sls_token_mock,
                     sls_user_info_no_sub_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})

            # assert 500 exception
            self.assertEqual(response.status_code, 500)
            content = json.loads(response.content)
            self.assertEqual(content['error'], ERROR_MSG_MYMEDICARE)

        # With HTTMock sls_user_info_empty_hicn_mock test User info HICN cannot be empty.
        with HTTMock(sls_token_mock,
                     sls_user_info_empty_hicn_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})

            # assert 500 exception
            self.assertEqual(response.status_code, 500)
            content = json.loads(response.content)
            self.assertEqual(content['error'], ERROR_MSG_MYMEDICARE)

        # With HTTMock sls_user_info_invalid_mbi_mock test User info HICN cannot be empty.
        with HTTMock(sls_token_mock,
                     sls_user_info_invalid_mbi_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})

            # assert 500 exception
            self.assertEqual(response.status_code, 500)
            content = json.loads(response.content)
            self.assertEqual(content['error'], ERROR_MSG_MYMEDICARE)

        # With HTTMock sls_token_http_error_mock to test BBMyMedicareCallbackAuthenticateSlsClientException
        with HTTMock(sls_token_http_error_mock,
                     sls_user_info_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})

            # assert 502 exception
            self.assertEqual(response.status_code, 502)
            content = json.loads(response.content)
            self.assertEqual(content['error'], ERROR_MSG_MYMEDICARE)

        # With HTTMock sls_user_info_http_error_mock to test BBMyMedicareCallbackAuthenticateSlsClientException
        with HTTMock(sls_token_mock,
                     sls_user_info_http_error_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})

            # assert 502 exception
            self.assertEqual(response.status_code, 502)
            content = json.loads(response.content)
            self.assertEqual(content['error'], ERROR_MSG_MYMEDICARE)
