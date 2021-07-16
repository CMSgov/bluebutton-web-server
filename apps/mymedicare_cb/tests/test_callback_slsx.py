import json
import io
import uuid

from datetime import datetime
from django.contrib.auth.models import Group, User
from django.utils.dateparse import parse_duration
from django.utils.text import slugify
from django.urls import reverse
from django.test.client import Client
from httmock import urlmatch, all_requests, HTTMock
from requests.exceptions import HTTPError
from rest_framework import status
from urllib.parse import urlparse, parse_qs

from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.models import Approval, Application
from apps.fhir.bluebutton.models import ArchivedCrosswalk, Crosswalk
from apps.mymedicare_cb.authorization import OAuth2ConfigSLSx
from apps.mymedicare_cb.models import AnonUserState
from apps.mymedicare_cb.tests.mock_url_responses_slsx import MockUrlSLSxResponses
from apps.mymedicare_cb.authorization import (BBMyMedicareSLSxUserinfoException, BBMyMedicareSLSxSignoutException)
from apps.mymedicare_cb.views import generate_nonce
from apps.test import BaseApiTest

from .responses import patient_response


loggers = [
    'audit.authenticate.mymedicare_cb',
]


class MyMedicareSLSxBlueButtonClientApiUserInfoTest(BaseApiTest):
    """
    Tests for the MyMedicare login and SLSx Callback
    """

    def setUp(self):
        self.callback_url = reverse('mymedicare-sls-callback')
        self.login_url = reverse('mymedicare-login')
        Group.objects.create(name='BlueButton')
        # Setup the RequestFactory
        self.client = Client()
        self._redirect_loggers(loggers)

    def tearDown(self):
        self._cleanup_logger()

    def _get_log_content(self, logger_name):
        return self._collect_logs(loggers).get(logger_name)

    def _get_log_lines_list(self, logger_name):
        buf = io.StringIO(self._get_log_content(logger_name))
        lines = buf.readlines()
        return lines

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

    def test_login_url_success(self):
        """
        Test well-formed login_url has expected content
        """
        fake_login_url = 'https://example.com/login?scope=openid'
        with self.settings(MEDICARE_SLSX_LOGIN_URI=fake_login_url, MEDICARE_SLSX_REDIRECT_URI='/123'):
            with HTTMock(MockUrlSLSxResponses.slsx_health_ok_mock):
                response = self.client.get(self.login_url + '?next=/')
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            query = parse_qs(urlparse(response['Location']).query)
            path = response['Location'].split('?')[0]
            self.assertEqual(path, 'https://example.com/login')
            self.assertEqual(query['redirect_uri'][0], '/123')
            self.assertTrue('relay' in query)

    def test_login_url_health_check_fail(self):
        """
        Test SLSx health check failure
        """
        fake_login_url = 'https://example.com/login?scope=openid'
        with self.settings(MEDICARE_SLSX_LOGIN_URI=fake_login_url, MEDICARE_SLSX_REDIRECT_URI='/123'):
            with HTTMock(MockUrlSLSxResponses.slsx_health_fail_mock):
                with self.assertRaises(HTTPError):
                    self.client.get(self.login_url + '?next=/')

    def test_callback_url_missing_relay(self):
        """
        Test callback_url returns HTTP 400 when
        necessary GET parameter relay (state) is missing.
        """
        response = self.client.get(self.callback_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authorize_uuid_dne(self):
        auth_uri = reverse(
            'oauth2_provider:authorize-instance',
            args=[uuid.uuid4()])
        response = self.client.get(auth_uri)
        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

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
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        approval.refresh_from_db()
        self.assertEqual(application, approval.application)
        self.assertNotIn('_auth_user_id', self.client.session)
        response = self.client.post(auth_uri, data={
            "client_id": "bad",
            "redirect_uri": "http://test.com",
            "response_type": "code"})
        self.assertEqual(status.HTTP_302_FOUND, response.status_code)
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://test.com',
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(auth_uri, data=payload)
        self.assertEqual(status.HTTP_302_FOUND, response.status_code)
        self.assertIn("code=", response.url)
        approval.created_at = datetime.now() - parse_duration("601")
        approval.save()
        response = self.client.post(auth_uri, data={
            "client_id": application.client_id,
            "redirect_uri": "http://test.com",
            "response_type": "code"})
        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

    def test_callback_url_success(self):
        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri="http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test")

        # mock fhir user info endpoint
        @urlmatch(netloc='fhir.backend.bluebutton.hhsdevcloud.us', path='/v1/fhir/Patient/')
        def fhir_patient_info_mock(url, request):
            return {
                'status_code': status.HTTP_200_OK,
                'content': patient_response,
            }

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
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
            response = self.client.get(self.callback_url, data={'req_token': '0000-test_req_token-0000', 'relay': state})
            # assert http redirect
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertIn("client_id=test", response.url)
            self.assertIn("redirect_uri=test.com", response.url)
            self.assertIn("response_type=token", response.url)
            self.assertIn("http://www.google.com/v1/o/authorize/", response.url)
            # assert login
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_callback_url_failure(self):
        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(state=state, next_uri="http://www.google.com")

        @all_requests
        def catchall(url, request):
            return {
                'status_code': status.HTTP_403_FORBIDDEN,
                'content': {'error': 'nope'},
            }

        with HTTMock(catchall):
            with self.assertRaises(HTTPError):
                self.client.get(self.callback_url, data={'req_token': '0000-test_req_token-0000', 'relay': state})

    def test_sls_token_exchange_w_creds(self):
        with self.settings(SLSX_CLIENT_ID="test",
                           SLSX_CLIENT_SECRET="stest"):

            sls_client = OAuth2ConfigSLSx()

            @all_requests
            def catchall(url, request):
                sls_auth_header = request.headers['Authorization']
                self.assertEqual(sls_auth_header, 'Basic dGVzdDpzdGVzdA==')
                return {
                    'status_code': status.HTTP_200_OK,
                    'content': {
                        'auth_token': 'test_tkn',
                        "user_id": "00112233-4455-6677-8899-aabbccddeeff",
                    },
                }

            with HTTMock(catchall):
                sls_client.exchange_for_access_token("test_code", None)
                self.assertEquals(sls_client.auth_token, "test_tkn")
                self.assertEquals(sls_client.user_id, "00112233-4455-6677-8899-aabbccddeeff")

    def test_failed_sls_token_exchange(self):
        with self.settings(SLSX_CLIENT_ID="test",
                           SLSX_CLIENT_SECRET="stest"):

            sls_client = OAuth2ConfigSLSx()

            @all_requests
            def catchall(url, request):
                sls_auth_header = request.headers['Authorization']
                self.assertEqual(sls_auth_header, 'Basic dGVzdDpzdGVzdA==')
                return {
                    'status_code': status.HTTP_401_UNAUTHORIZED,
                    'content': {
                        'error': 'nope!',
                    },
                }

            with HTTMock(catchall):
                with self.assertRaises(HTTPError):
                    sls_client.exchange_for_access_token("test_code", None)

    def test_callback_exceptions(self):
        # BB2-237: Added to test ASSERTS replaced with exceptions.
        #          These are typically for conditions that should never be reached, so generate a 500.
        ERROR_MSG_MYMEDICARE = "An error occurred connecting to account.mymedicare.gov"

        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri="http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test")

        # mock fhir user info endpoint
        @urlmatch(netloc='fhir.backend.bluebutton.hhsdevcloud.us', path='/v1/fhir/Patient/')
        def fhir_patient_info_mock(url, request):
            return {
                'status_code': status.HTTP_200_OK,
                'content': patient_response,
            }

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})
            # assert http redirect
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Change existing fhir_id prior to next test
        cw = Crosswalk.objects.get(id=1)
        saved_fhir_id = cw._fhir_id
        cw._fhir_id = "XXX"
        cw.save()

        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})

            # assert 500 exception
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            content = json.loads(response.content)
            self.assertEqual(content['error'], "Found user's fhir_id did not match")

        # Restore fhir_id
        cw = Crosswalk.objects.get(id=1)
        cw._fhir_id = saved_fhir_id
        cw.save()

        # With HTTMock sls_user_info_no_sub_mock that has no sub/username
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_no_username_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            with self.assertRaises(BBMyMedicareSLSxUserinfoException):
                response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})

        # With HTTMock sls_user_info_empty_hicn_mock test User info HICN cannot be empty.
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_empty_hicn_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})

            # assert 500 exception
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            content = json.loads(response.content)
            self.assertEqual(content['error'], ERROR_MSG_MYMEDICARE)

        # With HTTMock sls_user_info_invalid_mbi_mock test User info MBI is not in valid format.
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_invalid_mbi_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})

            # assert 500 exception
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            content = json.loads(response.content)
            self.assertEqual(content['error'], ERROR_MSG_MYMEDICARE)

        # With HTTMock sls_token_http_error_mock
        with HTTMock(MockUrlSLSxResponses.slsx_token_http_error_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            with self.assertRaises(HTTPError):
                response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})

            content = json.loads(response.content)
            self.assertEqual(content['error'], ERROR_MSG_MYMEDICARE)

        # With HTTMock sls_user_info_http_error_mock
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_http_error_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            with self.assertRaises(HTTPError):
                response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})

        # With HTTMock MockUrlSLSxResponses.slsx_signout_fail_mock has exception
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_fail_mock,
                     fhir_patient_info_mock,
                     catchall):
            with self.assertRaises(HTTPError):
                response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})

        # With HTTMock MockUrlSLSxResponses.slsx_signout_fail2_mock has exception
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_fail2_mock,
                     fhir_patient_info_mock,
                     catchall):
            with self.assertRaises(BBMyMedicareSLSxSignoutException):
                response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})

    def test_callback_allow_slsx_changes_to_hicn_and_mbi(self):
        '''
        This tests changed made to the matching logic per Jira BB2-612.
        This is to allow for MBI and HICN updates for beneficiaries as Long as the FHIR_ID still matches

        Two related/opposite tests were removed from test_callback_exceptions() and relocted here.

        TEST SUMMARY:

            NOTE: The fhir_patient_info_mock always provides a BFD patient resource search match to
                  a bene with fhir_id = -20140000008325

            1. First successful matching for beneficiary. This creates a new Crosswalk entry
               with hicn/mbi hash values used in the initial match.

            2. The bene's HICN has been changed in the mock SLSx user_info response.

               This is for the use case where a beneficary's HICN has been changed in the
               SLSx/BEDAP upstream identity service.

               This response is mocked by:  MockUrlSLSxResponses.slsx_user_info_mock_changed_hicn

               This would previously FAIL with response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
               with error text: "Found user's hicn did not match".

            3. Restore saved_hicn_hash in Crosswalk prior to next test. Restore crosswalk state to same as #1.

            4. The bene's MBI has been changed in the mock SLSx user_info response.
               This response is mocked by:  MockUrlSLSxResponses.slsx_user_info_mock_changed_mbi

            5. Restore saved_mbi_hash in Crosswalk prior to next test. Restore crosswalk state to same as #1.

            6. The bene's HICN & MBI (both) have been changed in the mock SLSx user_info response.
               This response is mocked by:  MockUrlSLSxResponses.slsx_user_info_mock_changed_hicn_mbi
        '''
        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri="http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test")

        # mock fhir user info endpoint with fhir_id == "-20140000008325"
        @urlmatch(netloc='fhir.backend.bluebutton.hhsdevcloud.us', path='/v1/fhir/Patient/')
        def fhir_patient_info_mock(url, request):
            return {
                'status_code': status.HTTP_200_OK,
                'content': patient_response,
            }

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        # 1. 1st sucessful matching for bene that creates a crosswalk entry
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})
            # assert http redirect
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Get crosswalk values.
        cw = Crosswalk.objects.get(id=1)

        # Assert correct crosswalk values:
        self.assertEqual(cw.user.id, 1)
        self.assertEqual(cw.user.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(cw.fhir_id, "-20140000008325")
        self.assertEqual(cw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(cw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # Save crosswalk values for restoring prior to later tests.
        saved_hicn_hash = cw._user_id_hash
        saved_mbi_hash = cw._user_mbi_hash

        # Validate ArchiveCrosswalk values
        self.assertEqual(ArchivedCrosswalk.objects.count(), 0)

        # 2. The bene's HICN has been changed in the mock SLSx user_info response.
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock_changed_hicn,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})
            # assert http redirect
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Get crosswalk values.
        cw = Crosswalk.objects.get(id=1)

        # Assert correct crosswalk values. Did the hicn update to new/changed value?
        self.assertEqual(cw.user.id, 1)
        self.assertEqual(cw.user.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(cw.fhir_id, "-20140000008325")
        self.assertEqual(cw._user_id_hash, "55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122")
        self.assertEqual(cw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # Validate crosswalk_updated in logging
        log_list = self._get_log_lines_list('audit.authenticate.mymedicare_cb')
        self.assertEqual(len(log_list), 3)

        # Get dict for last (3rd) log entry
        log_dict = json.loads(log_list[2])

        # Assert correct values
        self.assertEqual(log_dict['user_id'], 1)
        self.assertEqual(log_dict['username'], "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(log_dict['fhir_id'], "-20140000008325")
        self.assertEqual(log_dict['crosswalk_updated'], "H")
        self.assertEqual(log_dict['crosswalk']['user_hicn_hash'],
                         "55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122")
        self.assertEqual(log_dict['crosswalk']['user_mbi_hash'],
                         "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # Assert correct archived crosswalk values:
        self.assertEqual(ArchivedCrosswalk.objects.count(), 1)
        acw = ArchivedCrosswalk.objects.get(id=1)

        self.assertEqual(acw.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(acw._fhir_id, "-20140000008325")
        self.assertEqual(acw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(acw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # 3. Restore crosswalk's hicn hash to original.
        cw = Crosswalk.objects.get(id=1)
        cw._user_id_hash = saved_hicn_hash
        cw.save()

        # 4. The bene's MBI has been changed in the mock SLSx user_info response.
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock_changed_mbi,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})
            # assert http redirect
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Get crosswalk values.
        cw = Crosswalk.objects.get(id=1)

        # Assert correct crosswalk values. Did the hicn update to new/changed value?
        self.assertEqual(cw.user.id, 1)
        self.assertEqual(cw.user.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(cw.fhir_id, "-20140000008325")
        self.assertEqual(cw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(cw._user_mbi_hash, "e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0")

        # Validate crosswalk_updated in logging
        log_list = self._get_log_lines_list('audit.authenticate.mymedicare_cb')
        self.assertEqual(len(log_list), 4)

        # Get dict for last (4th) log entry
        log_dict = json.loads(log_list[3])

        # Assert correct values
        self.assertEqual(log_dict['user_id'], 1)
        self.assertEqual(log_dict['username'], "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(log_dict['fhir_id'], "-20140000008325")
        self.assertEqual(log_dict['crosswalk_updated'], "M")
        self.assertEqual(log_dict['crosswalk']['user_hicn_hash'],
                         "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(log_dict['crosswalk']['user_mbi_hash'],
                         "e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0")

        # Assert correct archived crosswalk values:
        self.assertEqual(ArchivedCrosswalk.objects.count(), 2)
        acw = ArchivedCrosswalk.objects.get(id=2)

        self.assertEqual(acw.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(acw._fhir_id, "-20140000008325")
        self.assertEqual(acw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(acw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # 5. Restore crosswalk's mbi hash to original.
        cw = Crosswalk.objects.get(id=1)
        cw._user_mbi_hash = saved_mbi_hash
        cw.save()

        # 6. The bene's HICN & MBI (both) have been changed in the mock SLSx user_info response.
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock_changed_hicn_mbi,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'req_token': 'test', 'relay': state})
            # assert http redirect
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Get crosswalk values.
        cw = Crosswalk.objects.get(id=1)

        # Assert correct crosswalk values. Did the hicn update to new/changed value?
        self.assertEqual(cw.user.id, 1)
        self.assertEqual(cw.user.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(cw.fhir_id, "-20140000008325")
        self.assertEqual(cw._user_id_hash, "55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122")
        self.assertEqual(cw._user_mbi_hash, "e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0")

        # Validate crosswalk_updated in logging
        log_list = self._get_log_lines_list('audit.authenticate.mymedicare_cb')
        self.assertEqual(len(log_list), 5)

        # Get dict for last (5th) log entry
        log_dict = json.loads(log_list[4])

        # Assert correct values
        self.assertEqual(log_dict['user_id'], 1)
        self.assertEqual(log_dict['username'], "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(log_dict['fhir_id'], "-20140000008325")
        self.assertEqual(log_dict['crosswalk_updated'], "HM")
        self.assertEqual(log_dict['crosswalk']['user_hicn_hash'],
                         "55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122")
        self.assertEqual(log_dict['crosswalk']['user_mbi_hash'],
                         "e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0")

        # Assert correct archived crosswalk values:
        self.assertEqual(ArchivedCrosswalk.objects.count(), 3)
        acw = ArchivedCrosswalk.objects.get(id=3)

        self.assertEqual(acw.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(acw._fhir_id, "-20140000008325")
        self.assertEqual(acw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(acw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")
