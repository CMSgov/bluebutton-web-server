import copy
import json
import jsonschema
import re
import uuid

import apps.logging.request_logger as logging

from datetime import datetime
from django.contrib.auth.models import Group, User
from django.utils.dateparse import parse_duration
from django.utils.text import slugify
from django.urls import reverse
from django.test.client import Client
from httmock import urlmatch, all_requests, HTTMock
from jsonschema import validate
from requests.exceptions import HTTPError
from rest_framework import status
from urllib.parse import urlparse, parse_qs

from apps.accounts.models import UserProfile
from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.models import Approval, Application
from apps.fhir.bluebutton.models import ArchivedCrosswalk, Crosswalk
from apps.mymedicare_cb.authorization import OAuth2ConfigSLSx
from apps.mymedicare_cb.models import AnonUserState
from apps.mymedicare_cb.tests.mock_url_responses_slsx import MockUrlSLSxResponses
from apps.mymedicare_cb.authorization import (BBMyMedicareSLSxUserinfoException, BBMyMedicareSLSxSignoutException)
from apps.mymedicare_cb.views import generate_nonce
from apps.logging.tests.audit_logger_schemas import MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA
from apps.test import BaseApiTest

from .responses import patient_response


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
        self._redirect_loggers()

    def tearDown(self):
        self._cleanup_logger()

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

    def validate_json_schema(self, schema, content):
        try:
            validate(instance=content, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            # Show error info for debugging
            print("jsonschema.exceptions.ValidationError: ", e)
            return False
        return True

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
        This tests changes made to the matching logic per Jira BB2-612.
        This is to allow for MBI and HICN updates for beneficiaries as long as the FHIR_ID still matches.

        Two related/opposite tests were removed from test_callback_exceptions() and relocated here.

        TEST SUMMARY:

            NOTE: The fhir_patient_info_mock always provides a BFD patient resource search match to
                  a bene with fhir_id = -20140000008325

            1. First successful matching for beneficiary having only a valid hicn and EMPTY mbi.
               This creates a new Crosswalk entry with hicn and NULL mbi hash values in the crosswalk.

            2. The bene's MBI has been changed from empty to valid value in the mock SLSx user_info response.
               The crosswalk is updated with the new MBI hash.

            3. Remove Crosswalk and ArchivedCrosswalk entries for a start fresh.

            4. Successful matching for beneficiary having valid hicn/mbi.
               This creates a new Crosswalk entry with hicn/mbi hash values used in the initial match.

            5. The bene's HICN has been changed in the mock SLSx user_info response.

               This is for the use case where a beneficary's HICN has been changed in the
               SLSx/BEDAP upstream identity service.

               This response is mocked by:  MockUrlSLSxResponses.slsx_user_info_mock_changed_hicn

               This would previously FAIL with response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
               with error text: "Found user's hicn did not match".

               The new behavior updates the HICN hash in the crosswalk.

            6. Restore saved_hicn_hash in Crosswalk prior to next test. Restore crosswalk state to same as #4.

            7. The bene's MBI has been changed in the mock SLSx user_info response.
               This response is mocked by:  MockUrlSLSxResponses.slsx_user_info_mock_changed_mbi

               The new behavior updates the MBI hash in the crosswalk.

            8. Restore saved_mbi_hash in Crosswalk prior to next test. Restore crosswalk state to same as #4.

            9. The bene's HICN & MBI (both) have been changed in the mock SLSx user_info response.
               This response is mocked by:  MockUrlSLSxResponses.slsx_user_info_mock_changed_hicn_mbi

               The new behavior updates the HICN & MBI hash in the crosswalk.
        '''
        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri="http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test")

        # mock fhir patient endpoint (back end bfd) with fhir_id == "-20140000008325"
        @urlmatch(netloc="fhir.backend.bluebutton.hhsdevcloud.us", path="/v1/fhir/Patient/")
        def fhir_patient_info_mock(url, request):
            return {
                "status_code": status.HTTP_200_OK,
                "content": patient_response,
            }

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        # 1. First successful matching for beneficiary having valid only hicn and EMPTY mbi.
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_empty_mbi_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={"req_token": "test", "relay": state})
            # assert http redirect
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Get crosswalk values.
        cw = Crosswalk.objects.get(id=1)

        # Assert correct crosswalk values:
        self.assertEqual(cw.user.id, 1)
        self.assertEqual(cw.user.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(cw.fhir_id, "-20140000008325")
        self.assertEqual(cw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(cw._user_mbi_hash, None)

        # Validate ArchiveCrosswalk count
        self.assertEqual(ArchivedCrosswalk.objects.count(), 0)

        # Validate logging
        log_list = self._get_log_lines_list(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER)
        self.assertEqual(len(log_list), 2)

        #   Get last log line
        log_dict = json.loads(log_list[len(log_list) - 1])

        #   Set working copy of schema
        log_schema = copy.deepcopy(MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA)

        #   Update json schema for what changed (mbi = None/Null).
        log_schema["properties"]["crosswalk"]["properties"].update({
            "user_id_type": {"pattern": "^H$"},
            "user_mbi_hash": {"type": "null"},
        })

        log_schema["properties"].update({
            "mbi_hash": {"type": "null"},
            "hash_lookup_type": {"pattern": "^H$"},
        })

        #   Assert correct log values using original json schema
        self.assertTrue(
            self.validate_json_schema(
                log_schema, log_dict
            )
        )

        # 2. The bene's MBI has been changed from empty to valid value in the mock SLSx user_info response.
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={"req_token": "test", "relay": state})
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

        # Assert correct archived crosswalk values:
        self.assertEqual(ArchivedCrosswalk.objects.count(), 1)
        acw = ArchivedCrosswalk.objects.get(id=1)

        self.assertEqual(acw.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(acw._fhir_id, "-20140000008325")
        self.assertEqual(acw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(acw._user_mbi_hash, None)

        # Validate logging
        log_list = self._get_log_lines_list(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER)
        self.assertEqual(len(log_list), 3)

        #   Get last log line
        log_dict = json.loads(log_list[len(log_list) - 1])

        #   Set working copy of schema
        log_schema = copy.deepcopy(MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA)

        #   Update json schema for what changed (mbi = None/Null).
        log_schema["properties"]["crosswalk"]["properties"].update({
            "user_id_type": {"pattern": "^M$"},
            "user_mbi_hash": {"type": "string",
                              "pattern": "^4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28$"},
        })

        log_schema["properties"].update({
            "mesg": {"pattern": "^RETURN existing beneficiary record$"},
            "mbi_updated": {"enum": [True]},
            "mbi_updated_from_null": {"enum": [True]},
            "mbi_hash": {"type": "string",
                         "pattern": "^4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28$"},
            "hash_lookup_type": {"type": "string", "pattern": "^M$"},
            "crosswalk_before": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "user_hicn_hash": {"type": "string",
                                       "pattern": "^f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948$"},
                    "user_mbi_hash": {"type": "null"},
                    "fhir_id": {"type": "string", "pattern": "^-20140000008325$"},
                    "user_id_type": {"type": "string", "pattern": "^H$"}
                }
            }
        })

        #   Assert correct log values using original json schema
        self.assertTrue(
            self.validate_json_schema(
                log_schema, log_dict
            )
        )

        # 3. Remove User (cascade removes UserProfile/Crosswalk) and ArchivedCrosswalk entries for a fresh start.
        User.objects.filter(username="00112233-4455-6677-8899-aabbccddeeff").delete()
        ArchivedCrosswalk.objects.filter(id=1).delete()

        #   Assert counts
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(UserProfile.objects.count(), 0)
        self.assertEqual(Crosswalk.objects.count(), 0)
        self.assertEqual(ArchivedCrosswalk.objects.count(), 0)

        # 4. 1st sucessful matching for bene that creates a new crosswalk entry
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={"req_token": "test", "relay": state})
            # assert http redirect
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Get crosswalk values.
        cw = Crosswalk.objects.get(id=2)

        # Assert correct crosswalk values:
        self.assertEqual(cw.user.id, 2)
        self.assertEqual(cw.user.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(cw.fhir_id, "-20140000008325")
        self.assertEqual(cw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(cw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # Validate ArchiveCrosswalk count
        self.assertEqual(ArchivedCrosswalk.objects.count(), 0)

        # Validate logging
        log_list = self._get_log_lines_list(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER)
        self.assertEqual(len(log_list), 5)

        #   Get last log line
        log_dict = json.loads(log_list[len(log_list) - 1])

        #   Set working copy of schema
        log_schema = copy.deepcopy(MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA)

        #   Assert correct log values using original json schema
        self.assertTrue(
            self.validate_json_schema(
                MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA, log_dict
            )
        )

        # Save crosswalk values for restoring prior to later tests.
        saved_hicn_hash = cw._user_id_hash
        saved_mbi_hash = cw._user_mbi_hash

        # 5. The bene's HICN has been changed in the mock SLSx user_info response.
        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_mock_changed_hicn,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={"req_token": "test", "relay": state})
            # assert http redirect
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Get crosswalk values.
        cw = Crosswalk.objects.get(id=2)

        # Assert correct crosswalk values. Did the hicn update to new value?
        self.assertEqual(cw.user.id, 2)
        self.assertEqual(cw.user.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(cw.fhir_id, "-20140000008325")
        self.assertEqual(cw._user_id_hash, "55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122")
        self.assertEqual(cw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # Assert correct archived crosswalk values:
        self.assertEqual(ArchivedCrosswalk.objects.count(), 1)
        acw = ArchivedCrosswalk.objects.get(id=2)

        self.assertEqual(acw.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(acw._fhir_id, "-20140000008325")
        self.assertEqual(acw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(acw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # Validate logging
        log_list = self._get_log_lines_list(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER)

        #   Validate log lines count
        self.assertEqual(len(log_list), 6)

        #   Get last log line
        log_dict = json.loads(log_list[len(log_list) - 1])

        #   Set working copy of schema
        log_schema = copy.deepcopy(MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA)

        #   Update json schema for what changed (hicn). Add crosswalk_before to also be used later.
        log_schema["properties"]["crosswalk"]["properties"].update({
            "user_hicn_hash": {"type": "string",
                               "pattern": "^55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122$"}})

        log_schema["properties"].update({
            "mesg": {"type": "string", "pattern": "^RETURN existing beneficiary record$"},
            "hicn_updated": {"enum": [True]},
            "hicn_hash": {"type": "string",
                          "pattern": "^55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122$"},
            "crosswalk_before": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "user_hicn_hash": {"type": "string",
                                       "pattern": "^f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948$"},
                    "user_mbi_hash": {"type": "string",
                                      "pattern": "^4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28$"},
                    "fhir_id": {"type": "string", "pattern": "^-20140000008325$"},
                    "user_id_type": {"type": "string", "pattern": "^M$"}
                }
            }
        })

        #   Assert correct log values using json schema
        self.assertTrue(
            self.validate_json_schema(
                log_schema, log_dict
            )
        )

        # 6. Restore crosswalk's hicn hash to original.
        cw = Crosswalk.objects.get(id=2)
        cw._user_id_hash = saved_hicn_hash
        cw.save()

        # 7. The bene's MBI has been changed in the mock SLSx user_info response.
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
        cw = Crosswalk.objects.get(id=2)

        # Assert correct crosswalk values. Did the hicn update to new/changed value?
        self.assertEqual(cw.user.id, 2)
        self.assertEqual(cw.user.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(cw.fhir_id, "-20140000008325")
        self.assertEqual(cw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(cw._user_mbi_hash, "e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0")

        # Assert correct archived crosswalk values
        self.assertEqual(ArchivedCrosswalk.objects.count(), 2)
        acw = ArchivedCrosswalk.objects.get(id=2)

        self.assertEqual(acw.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(acw._fhir_id, "-20140000008325")
        self.assertEqual(acw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(acw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # Validate logging
        log_list = self._get_log_lines_list(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER)
        self.assertEqual(len(log_list), 7)

        #   Get last log line
        log_dict = json.loads(log_list[len(log_list) - 1])

        #   Set working copy of schema
        log_schema = copy.deepcopy(MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA)

        #   Update json schema for what changed (mbi)
        log_schema["properties"]["crosswalk"]["properties"].update({
            "user_mbi_hash": {"type": "string", "pattern": "^e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0$"}})

        log_schema["properties"].update({
            "mesg": {"type": "string", "pattern": "^RETURN existing beneficiary record$"},
            "mbi_updated": {"enum": [True]},
            "mbi_hash": {"type": "string", "pattern": "^e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0$"},
            "crosswalk_before": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "user_hicn_hash": {"type": "string",
                                       "pattern": "^f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948$"},
                    "user_mbi_hash": {"type": "string",
                                      "pattern": "^4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28$"},
                    "fhir_id": {"type": "string", "pattern": "^-20140000008325$"},
                    "user_id_type": {"type": "string", "pattern": "^M$"}
                }
            }
        })

        #   Assert correct log values using json schema
        self.assertTrue(
            self.validate_json_schema(
                log_schema, log_dict
            )
        )

        # 8. Restore crosswalk's mbi hash to original.
        cw = Crosswalk.objects.get(id=2)
        cw._user_mbi_hash = saved_mbi_hash
        cw.save()

        # 9. The bene's HICN & MBI (both) have been changed in the mock SLSx user_info response.
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
        cw = Crosswalk.objects.get(id=2)

        # Assert correct crosswalk values. Did the hicn update to new/changed value?
        self.assertEqual(cw.user.id, 2)
        self.assertEqual(cw.user.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(cw.fhir_id, "-20140000008325")
        self.assertEqual(cw._user_id_hash, "55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122")
        self.assertEqual(cw._user_mbi_hash, "e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0")

        # Assert correct archived crosswalk values:
        self.assertEqual(ArchivedCrosswalk.objects.count(), 3)
        acw = ArchivedCrosswalk.objects.get(id=3)

        self.assertEqual(acw.username, "00112233-4455-6677-8899-aabbccddeeff")
        self.assertEqual(acw._fhir_id, "-20140000008325")
        self.assertEqual(acw._user_id_hash, "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948")
        self.assertEqual(acw._user_mbi_hash, "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28")

        # Validate logging
        log_list = self._get_log_lines_list(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER)
        self.assertEqual(len(log_list), 8)

        #   Get last line
        log_dict = json.loads(log_list[len(log_list) - 1])

        #   Set working copy of schema
        log_schema = copy.deepcopy(MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA)

        #   Update json schema for what changed (mbi and hicn)
        log_schema["properties"]["crosswalk"]["properties"].update({
            "user_hicn_hash": {"type": "string",
                               "pattern": "^55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122$"},
            "user_mbi_hash": {"type": "string",
                              "pattern": "^e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0$"}})

        log_schema["properties"].update({
            "mesg": {"type": "string", "pattern": "^RETURN existing beneficiary record$"},
            "hicn_updated": {"enum": [True]},
            "mbi_updated": {"enum": [True]},
            "hicn_hash": {"type": "string",
                          "pattern": "^55accb0603dcca1fb171e86a3ded3ead1b9f12155cf3e41327c53730890e6122$"},
            "mbi_hash": {"type": "string",
                         "pattern": "^e9ae977f531e29e4a3cb4435984e78467ca816db18920de8d6e5056d424935a0$"},
            "crosswalk_before": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "user_hicn_hash": {"type": "string",
                                       "pattern": "^f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948$"},
                    "user_mbi_hash": {"type": "string",
                                      "pattern": "^4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28$"},
                    "fhir_id": {"type": "string", "pattern": "^-20140000008325$"},
                    "user_id_type": {"type": "string", "pattern": "^M$"},
                }
            },
        })

        #   Assert correct log values using json schema
        self.assertTrue(
            self.validate_json_schema(
                log_schema, log_dict
            )
        )

    def test_callback_usr_info_hicn_none(self):
        # BB2-850
        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri="http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test")

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        with HTTMock(MockUrlSLSxResponses.slsx_token_mock,
                     MockUrlSLSxResponses.slsx_user_info_none_hicn_mock,
                     MockUrlSLSxResponses.slsx_health_ok_mock,
                     MockUrlSLSxResponses.slsx_signout_ok_mock,
                     catchall):
            s = self.client.session
            s.update({"auth_uuid": "84b4afdc-d85d-4ea4-b44c-7bde77634429",
                      "auth_app_id": "2",
                      "auth_app_name": "TestApp-001",
                      "auth_client_id": "uouIr1mnblrv3z0PJHgmeHiYQmGVgmk5DZPDNfop"})
            s.save()
            response = self.client.get(self.callback_url, data={'req_token': '0000-test_req_token-0000', 'relay': state})
            resp_json = response.json()
            self.assertEqual(response.status_code, 500)
            self.assertIsNotNone(resp_json)
            self.assertIsNotNone(resp_json.get("error"))
            self.assertEqual(resp_json.get("error"), "An error occurred connecting to account.mymedicare.gov")
            # further check log for root cause
            sls_authn_log_content = self._get_log_content(logging.AUDIT_AUTHN_SLS_LOGGER)
            self.assertIsNotNone(sls_authn_log_content)
            quoted_strings = re.findall("{[^{}]+}", sls_authn_log_content)
            # expect one log record
            self.assertEqual(len(quoted_strings), 1)
            log_rec_json = json.loads(quoted_strings[0])
            self.assertIsNotNone(log_rec_json)
            self.assertEqual(log_rec_json.get("sls_status_mesg"), "User info HICN cannot be empty or None.")
