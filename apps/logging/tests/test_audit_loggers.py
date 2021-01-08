import re
import json

from django.urls import reverse
from django.test.client import Client
from django.contrib.auth.models import Group
from httmock import all_requests, HTTMock, urlmatch
from waffle.testutils import override_switch

from apps.dot_ext.models import Application
from apps.test import BaseApiTest
from apps.mymedicare_cb.views import generate_nonce
from apps.mymedicare_cb.models import AnonUserState
from apps.mymedicare_cb.tests.responses import patient_response
from apps.mymedicare_cb.tests.mock_url_responses_slsx import MockUrlSLSxResponses

loggers = [
    'audit.authorization.token',
    'audit.authorization.sls',
    'audit.data.fhir',
    'audit.authenticate.sls',
    'audit.authenticate.mymedicare_cb',
    'audit.authenticate.match_fhir_id',
    'audit.hhs_oauth_server.request_logging'
]


class HTTMockWithResponseHook(HTTMock):

    def intercept(self, request, **kwargs):
        response = super().intercept(request, **kwargs)
        # process hooks - we only have response hook for now
        self.dispatch_hook("response", request.hooks, response, **kwargs)
        return response

    def dispatch_hook(self, key, hooks, hook_data, **kwargs):
        """Dispatches a hook dictionary on a given piece of data."""
        hooks = hooks or {}
        hooks = hooks.get(key)
        if hooks:
            if hasattr(hooks, '__call__'):
                hooks = [hooks]
            for hook in hooks:
                _hook_data = hook(hook_data, **kwargs)
                if _hook_data is not None:
                    hook_data = _hook_data
        return hook_data


class TestAuditEventLoggers(BaseApiTest):

    def setUp(self):
        Group.objects.create(name='BlueButton')
        self.callback_url = reverse('mymedicare-sls-callback')
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])
        self._create_capability('patient', [
            ["GET", r"\/v1\/fhir\/Patient\/\-\d+"],
            ["GET", "/v1/fhir/Patient"],
        ])
        # Setup the RequestFactory
        self.client = Client()
        self._redirect_loggers(loggers)

    def tearDown(self):
        self._cleanup_logger()

    def get_log_content(self, logger_name):
        return self._collect_logs(loggers).get(logger_name)

    def test_fhir_events_logging(self):
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            fhir_log_content = self.get_log_content('audit.data.fhir')
            self.assertIsNotNone(fhir_log_content)

            # Validate FHIR Patient response
            log_entry_dict = json.loads(fhir_log_content)
            """
            Example log_entry_dict entry:
            {   'application': {'id': '1', 'name': 'John_Smith_test', 'user': {'id': '1'}},
                'fhir_id': '-20140000008325',
                'includeAddressFields': 'False',
                'path': '/v1/fhir/Patient',
                'start_time': '2021-01-08 16:14:49.041219',
                'type': 'fhir_pre_fetch',
                'user': 'patientId:-20140000008325',
                'uuid': 'a18bec1c-51cc-11eb-b863-0242ac120003'}
            """
            compare_dict = {'application': {'id': '1', 'name': 'John_Smith_test', 'user': {'id': '1'}},
                            'fhir_id': '-20140000008325',
                            'includeAddressFields': 'False',
                            'path': '/v1/fhir/Patient',
                            'type': 'fhir_pre_fetch',
                            'user': 'patientId:-20140000008325'}
            self.assert_log_entry_valid(log_entry_dict, compare_dict, ['start_time', 'uuid'], None)

            return {
                'status_code': 200,
                # TODO replace this with true backend response, this has been post proccessed
                'content': patient_response,
            }

        with HTTMock(catchall):
            self.client.get(
                reverse('bb_oauth_fhir_patient_search'),
                {'count': 5, 'hello': 'world'},
                Authorization="Bearer %s" % (first_access_token))

            # fhir_log_content, token_log_content
            # check fhir log content
            fhir_log_content = self.get_log_content('audit.data.fhir')
            self.assertIsNotNone(fhir_log_content)
            log_entries = fhir_log_content.splitlines()

            # Validate fhir_pre_fetch entry
            log_entry_dict = json.loads(log_entries[0])
            compare_dict = {'application': {'id': '1', 'name': 'John_Smith_test', 'user': {'id': '1'}},
                            'fhir_id': '-20140000008325',
                            'includeAddressFields': 'False',
                            'path': '/v1/fhir/Patient',
                            'type': 'fhir_pre_fetch',
                            'user': 'patientId:-20140000008325'}
            self.assert_log_entry_valid(log_entry_dict, compare_dict, ['start_time', 'uuid'], None)

            # Validate fhir_post_fetch entry
            log_entry_dict = json.loads(log_entries[1])
            """
            Example log_entry_dict:
            {   'application': {'id': '1', 'name': 'John_Smith_test', 'user': {'id': '1'}},
                'code': 200,
                'elapsed': 0.0,
                'fhir_id': '-20140000008325',
                'includeAddressFields': 'False',
                'path': '/v1/fhir/Patient',
                'size': 1270,
                'start_time': '2021-01-08 16:18:54.717788',
                'type': 'fhir_post_fetch',
                'user': 'patientId:-20140000008325',
                'uuid': '33fb312a-51cd-11eb-a21d-0242ac120003'}
            """
            compare_dict = {'application': {'id': '1', 'name': 'John_Smith_test', 'user': {'id': '1'}},
                            'code': 200,
                            'fhir_id': '-20140000008325',
                            'includeAddressFields': 'False',
                            'path': '/v1/fhir/Patient',
                            'size': 1270,
                            'type': 'fhir_post_fetch',
                            'user': 'patientId:-20140000008325'}
            self.assert_log_entry_valid(log_entry_dict, compare_dict, ['start_time', 'uuid', 'elapsed'], None)

            # Validate AccessToken entry
            token_log_content = self.get_log_content('audit.authorization.token')
            self.assertIsNotNone(token_log_content)
            log_entries = token_log_content.splitlines()

            log_entry_dict = json.loads(log_entries[0])
            """
            Example log_entry_dict:
            {   'access_token': 'dc4d1d793108af4476a87f712f7553d2612e39315e07e977ee98d73b0fc1a374',
                'action': 'authorized',
                'application': {   'id': 1,
                                   'name': 'John_Smith_test',
                                   'user': {'id': 1, 'username': 'John'}},
                'auth_grant_type': 'password',
                'id': 1,
                'scopes': 'read write patient',
                'type': 'AccessToken',
                'user': {'id': 1, 'username': 'John'}}
            """
            compare_dict = {'action': 'authorized',
                            'application': {'id': 1,
                                            'name': 'John_Smith_test',
                                            'user': {'id': 1, 'username': 'John'}},
                            'auth_grant_type': 'password',
                            'id': 1,
                            'scopes': 'read write patient',
                            'type': 'AccessToken',
                            'user': {'id': 1, 'username': 'John'}}
            self.assert_log_entry_valid(log_entry_dict, compare_dict, ['access_token'], None)

    @override_switch('slsx-enable', active=True)
    def test_callback_url_success_slsx_logger(self):
        # copy and adapted for SLS logger test
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri="http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test")

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

        with HTTMockWithResponseHook(MockUrlSLSxResponses.slsx_token_mock,
                                     MockUrlSLSxResponses.slsx_user_info_mock,
                                     fhir_patient_info_mock,
                                     catchall):
            s = self.client.session
            s.update({"auth_uuid": "84b4afdc-d85d-4ea4-b44c-7bde77634429",
                      "auth_app_id": "2",
                      "auth_app_name": "TestApp-001",
                      "auth_client_id": "uouIr1mnblrv3z0PJHgmeHiYQmGVgmk5DZPDNfop"})
            s.save()
            self.client.get(self.callback_url, data={'req_token': 'xxxx-request-token-xxxx', 'state': state})

            slsx_log_content = self.get_log_content('audit.authorization.sls')

            quoted_strings = re.findall("{[^{}]+}", slsx_log_content)
            self.assertEqual(len(quoted_strings), 2)

            # Validate token response
            slsx_token_dict = json.loads(quoted_strings[0])
            """
            Example slsx_token_dict entry:
            {   'auth_token': '5afa715c1250f987fa4ac4cdcfc8d4174f0ae34e48f85a59935f7e7397d084a5',
                'code': 200,
                'elapsed': 0.0,
                'path': '/sso/session',
                'size': 183,
                'start_time': '2021-01-08 15:00:31.781767',
                'type': 'SLSx_token',
                'uuid': '40cf7222-51c2-11eb-854f-0242ac120003'}
            """
            compare_dict = {
                'code': 200,
                'path': '/sso/session',
                'type': 'SLSx_token'
            }
            remove_list = [
                'size',
                'elapsed',
                'start_time',
                'auth_token',
                'uuid'
            ]
            hasvalue_list = [
                'auth_token',
                'uuid'
            ]
            self.assert_log_entry_valid(slsx_token_dict, compare_dict, remove_list, hasvalue_list)

            # Validate userinfo response
            slsx_userinfo_dict = json.loads(quoted_strings[1])
            """
            Example slsx_userinfo_dict entry:
            {   'code': 200,
                'elapsed': 0.0,
                'path': '/v1/users/00112233-4455-6677-8899-aabbccddeeff',
                'size': 249,
                'start_time': '2021-01-08 15:09:11.888342',
                'sub': '00112233-4455-6677-8899-aabbccddeeff',
                'type': 'SLSx_userinfo',
                'uuid': '76d1390e-51c3-11eb-b4cd-0242ac120003'}
            """
            compare_dict = {
                'code': 200,
                'path': '/v1/users/00112233-4455-6677-8899-aabbccddeeff',
                'sub': '00112233-4455-6677-8899-aabbccddeeff',
                'type': 'SLSx_userinfo'
            }
            remove_list = [
                'size',
                'elapsed',
                'start_time',
                'uuid'
            ]
            hasvalue_list = [
                'uuid'
            ]
            self.assert_log_entry_valid(slsx_userinfo_dict, compare_dict, remove_list, hasvalue_list)

            authn_sls_log_content = self.get_log_content('audit.authenticate.sls')
            log_entries = authn_sls_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)

            # Validate Authentication:start entry
            log_entry_dict = json.loads(log_entries[0])
            """
            Example log_entry_dict:
            {   'sls_hicn_hash': 'f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948',
                'sls_mbi_format_msg': 'Valid',
                'sls_mbi_format_synthetic': True,
                'sls_mbi_format_valid': True,
                'sls_mbi_hash': '4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28',
                'sls_status': 'OK',
                'sls_status_mesg': None,
                'sub': '00112233-4455-6677-8899-aabbccddeeff',
                'type': 'Authentication:start'}
            """
            compare_dict = {
                'sls_mbi_format_msg': 'Valid',
                'sls_mbi_format_synthetic': True,
                'sls_mbi_format_valid': True,
                'sls_status': 'OK',
                'sls_status_mesg': None,
                'sub': '00112233-4455-6677-8899-aabbccddeeff',
                'type': 'Authentication:start'
            }
            remove_list = [
                'sls_hicn_hash',
                'sls_mbi_hash'
            ]
            hasvalue_list = [
                'sls_hicn_hash',
                'sls_mbi_hash'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            # Validate Authentication:success entry
            log_entry_dict = json.loads(log_entries[1])
            """
            Example log_entry_dict:
            {   'auth_crosswalk_action': 'C',
                'sub': '00112233-4455-6677-8899-aabbccddeeff',
                'type': 'Authentication:success',
                'user': {   'crosswalk': {   'fhir_id': '-20140000008325',
                                             'id': 1,
                                             'user_hicn_hash': 'f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948',
                                             'user_id_type': 'M',
                                             'user_mbi_hash': '4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28'},
                            'id': 1,
                            'username': '00112233-4455-6677-8899-aabbccddeeff'}}
            """
            compare_dict = {
                'auth_crosswalk_action': 'C',
                'sub': '00112233-4455-6677-8899-aabbccddeeff',
                'type': 'Authentication:success',
            }
            remove_list = [
                'user'
            ]
            hasvalue_list = [
                'user'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            mymedicare_cb_log_content = self.get_log_content('audit.authenticate.mymedicare_cb')
            log_entries = mymedicare_cb_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)

            # Validate mymedicare_cb:create_beneficiary_record entry
            log_entry_dict = json.loads(log_entries[0])
            """
            Example log_entry_dict:
            {   'fhir_id': '-20140000008325',
                'mesg': 'CREATE beneficiary record',
                'status': 'OK',
                'type': 'mymedicare_cb:create_beneficiary_record',
                'user_hicn_hash': 'f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948',
                'user_mbi_hash': '4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28',
                'username': '00112233-4455-6677-8899-aabbccddeeff'}
            """
            compare_dict = {
                'fhir_id': '-20140000008325',
                'mesg': 'CREATE beneficiary record',
                'status': 'OK',
                'type': 'mymedicare_cb:create_beneficiary_record',
                'username': '00112233-4455-6677-8899-aabbccddeeff'
            }
            remove_list = [
                'user_hicn_hash',
                'user_mbi_hash'
            ]
            hasvalue_list = [
                'user_hicn_hash',
                'user_mbi_hash'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            # Validate mymedicare_cb:get_and_update_user entry
            log_entry_dict = json.loads(log_entries[1])
            """
            Example log_entry_dict:
            {   'crosswalk': {   'fhir_id': '-20140000008325',
                                 'id': 1,
                                 'user_hicn_hash': 'f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948',
                                 'user_id_type': 'M',
                                 'user_mbi_hash': '4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28'},
                'fhir_id': '-20140000008325',
                'hash_lookup_type': 'M',
                'hicn_hash': 'f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948',
                'mbi_hash': '4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28',
                'mesg': 'CREATE beneficiary record',
                'status': 'OK',
                'type': 'mymedicare_cb:get_and_update_user'}
            """
            compare_dict = {
                'fhir_id': '-20140000008325',
                'hash_lookup_type': 'M',
                'mesg': 'CREATE beneficiary record',
                'status': 'OK',
                'type': 'mymedicare_cb:get_and_update_user'
            }
            remove_list = [
                'crosswalk',
                'hicn_hash',
                'mbi_hash',
            ]
            hasvalue_list = [
                'crosswalk',
                'hicn_hash',
                'mbi_hash'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            fhir_log_content = self.get_log_content('audit.data.fhir')
            log_entries = fhir_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)

            # Validate fhir_auth_pre_fetch entry
            log_entry_dict = json.loads(log_entries[0])
            """
            Example log_entry_dict:
            {   'includeAddressFields': 'False',
                'path': 'patient search',
                'start_time': '2021-01-08 16:55:12.127467',
                'type': 'fhir_auth_pre_fetch',
                'uuid': '45d18aac-51d2-11eb-a494-0242ac120003'}
            """
            compare_dict = {
                'includeAddressFields': 'False',
                'path': 'patient search',
                'type': 'fhir_auth_pre_fetch',
            }
            remove_list = [
                'start_time',
                'uuid'
            ]
            hasvalue_list = [
                'start_time',
                'uuid'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            # Validate fhir_auth_post_fetch entry
            log_entry_dict = json.loads(log_entries[1])
            """
            Example log_entry_dict:
            {   'code': 200,
                'elapsed': 0.0,
                'includeAddressFields': 'False',
                'path': 'patient search',
                'size': 1270,
                'start_time': '2021-01-08 16:56:52.608630',
                'type': 'fhir_auth_post_fetch',
                'uuid': '81b5c01a-51d2-11eb-9a2d-0242ac120003'}
            """
            compare_dict = {
                'code': 200,
                'includeAddressFields': 'False',
                'path': 'patient search',
                'type': 'fhir_auth_post_fetch',
            }
            remove_list = [
                'elapsed',
                'size',
                'start_time',
                'uuid'
            ]
            hasvalue_list = [
                'elapsed',
                'size',
                'start_time',
                'uuid'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            match_fhir_id_log_content = self.get_log_content('audit.authenticate.match_fhir_id')
            log_entries = match_fhir_id_log_content.splitlines()
            self.assertGreater(len(log_entries), 0)

            # Validate fhir.server.authentication.match_fhir_id entry
            log_entry_dict = json.loads(log_entries[0])
            """
            Example log_entry_dict:
            {   'auth_app_id': None,
                'auth_app_name': None,
                'auth_client_id': None,
                'auth_pkce_method': None,
                'auth_uuid': None,
                'fhir_id': '-20140000008325',
                'hash_lookup_mesg': 'FOUND beneficiary via mbi_hash',
                'hash_lookup_type': 'M',
                'hicn_hash': 'f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948',
                'match_found': True,
                'mbi_hash': '4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28',
                'type': 'fhir.server.authentication.match_fhir_id'}
            """
            compare_dict = {
                'fhir_id': '-20140000008325',
                'hash_lookup_mesg': 'FOUND beneficiary via mbi_hash',
                'hash_lookup_type': 'M',
                'match_found': True,
                'type': 'fhir.server.authentication.match_fhir_id'
            }
            remove_list = [
                'auth_app_id',
                'auth_app_name',
                'auth_client_id',
                'auth_pkce_method',
                'hicn_hash',
                'mbi_hash',
                'auth_uuid'
            ]
            hasvalue_list = [
                'hicn_hash',
                'mbi_hash'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            hhs_oauth_server_log_content = self.get_log_content('audit.hhs_oauth_server.request_logging')
            log_entries = hhs_oauth_server_log_content.splitlines()
            self.assertGreater(len(log_entries), 0)

            # Validate hhs_oauth_server request/response custom middleware log entry
            log_entry_dict = json.loads(log_entries[0])
            """
            Example log_entry_dict:
            {   'access_token_hash': '',
                'app_id': '',
                'app_name': '',
                'auth_crosswalk_action': 'C',
                'dev_id': '',
                'dev_name': '',
                'end_time': 1610125194.105491,
                'fhir_id': '-20140000008325',
                'ip_addr': '127.0.0.1',
                'location': '',
                'path': '/mymedicare/sls-callback',
                'request_uuid': 'ede19390-51d2-11eb-b3a2-0242ac120003',
                'response_code': 400,
                'size': 44,
                'start_time': 1610125194.089803,
                'user': '00112233-4455-6677-8899-aabbccddeeff'}
            """
            compare_dict = {
                'auth_crosswalk_action': 'C',
                'fhir_id': '-20140000008325',
                'ip_addr': '127.0.0.1',
                'path': '/mymedicare/sls-callback',
                'response_code': 400,
                'user': '00112233-4455-6677-8899-aabbccddeeff'
            }
            remove_list = [
                'access_token_hash',
                'app_id',
                'app_name',
                'dev_id',
                'dev_name',
                'end_time',
                'location',
                'request_uuid',
                'size',
                'start_time'
            ]
            hasvalue_list = [
                'end_time',
                'request_uuid',
                'size',
                'start_time',
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

    @override_switch('slsx-enable', active=False)
    def test_callback_url_success_sls_logger(self):
        # TODO: Remove this test after migrated to SLSx
        # copy and adapted for SLS logger test
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

        with HTTMockWithResponseHook(sls_token_mock,
                                     sls_user_info_mock,
                                     fhir_patient_info_mock,
                                     catchall):
            s = self.client.session
            s.update({"auth_uuid": "84b4afdc-d85d-4ea4-b44c-7bde77634429",
                      "auth_app_id": "2",
                      "auth_app_name": "TestApp-001",
                      "auth_client_id": "uouIr1mnblrv3z0PJHgmeHiYQmGVgmk5DZPDNfop"})
            s.save()
            self.client.get(self.callback_url, data={'code': 'test', 'state': state})

            sls_log_content = self.get_log_content('audit.authorization.sls')

            quoted_strings = re.findall("{[^{}]+}", sls_log_content)
            self.assertEqual(len(quoted_strings), 2)
            sls_token_dict = json.loads(quoted_strings[0])
            compare_dict = {
                'code': 200,
                'path': '/v1/oauth/token',
                'type': 'SLS_token'
            }
            remove_list = [
                'size',
                'elapsed',
                'start_time',
                'access_token',
                'uuid'
            ]
            hasvalue_list = [
                'access_token',
                'uuid'
            ]
            self.assert_log_entry_valid(sls_token_dict, compare_dict, remove_list, hasvalue_list)

            sls_userinfo_dict = json.loads(quoted_strings[1])
            compare_dict = {
                'code': 200,
                'path': '/v1/oauth/userinfo',
                'sub': '00112233-4455-6677-8899-aabbccddeeff',
                'type': 'SLS_userinfo',
            }
            remove_list = [
                'elapsed',
                'size',
                'start_time',
                'uuid'
            ]
            hasvalue_list = [
                'uuid'
            ]
            self.assert_log_entry_valid(sls_userinfo_dict, compare_dict, remove_list, hasvalue_list)

            authn_sls_log_content = self.get_log_content('audit.authenticate.sls')
            log_entries = authn_sls_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)
            # Authentication:start
            log_entry_dict = json.loads(log_entries[0])
            compare_dict = {
                'sls_mbi_format_msg': 'Valid',
                'sls_mbi_format_synthetic': True,
                'sls_mbi_format_valid': True,
                'sls_status': 'OK',
                'sls_status_mesg': None,
                'sub': '00112233-4455-6677-8899-aabbccddeeff',
                'type': 'Authentication:start'
            }
            remove_list = [
                'sls_hicn_hash',
                'sls_mbi_hash'
            ]
            hasvalue_list = [
                'sls_hicn_hash',
                'sls_mbi_hash'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)
            log_entry_dict = json.loads(log_entries[1])
            compare_dict = {
                'auth_crosswalk_action': 'C',
                'sub': '00112233-4455-6677-8899-aabbccddeeff',
                'type': 'Authentication:success',
            }
            remove_list = [
                'user'
            ]
            hasvalue_list = [
                'user'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            mymedicare_cb_log_content = self.get_log_content('audit.authenticate.mymedicare_cb')
            log_entries = mymedicare_cb_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)
            # mymedicare_cb:create_beneficiary_record
            log_entry_dict = json.loads(log_entries[0])

            compare_dict = {
                'fhir_id': '-20140000008325',
                'mesg': 'CREATE beneficiary record',
                'status': 'OK',
                'type': 'mymedicare_cb:create_beneficiary_record',
                'username': '00112233-4455-6677-8899-aabbccddeeff'
            }
            remove_list = [
                'user_hicn_hash',
                'user_mbi_hash'
            ]
            hasvalue_list = [
                'user_hicn_hash',
                'user_mbi_hash'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            # mymedicare_cb:get_and_update_user
            log_entry_dict = json.loads(log_entries[1])

            compare_dict = {
                'fhir_id': '-20140000008325',
                'hash_lookup_type': 'M',
                'mesg': 'CREATE beneficiary record',
                'status': 'OK',
                'type': 'mymedicare_cb:get_and_update_user'
            }
            remove_list = [
                'crosswalk',
                'hicn_hash',
                'mbi_hash',
            ]
            hasvalue_list = [
                'crosswalk',
                'hicn_hash',
                'mbi_hash'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            fhir_log_content = self.get_log_content('audit.data.fhir')
            log_entries = fhir_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)
            # fhir_auth_pre_fetch
            log_entry_dict = json.loads(log_entries[0])

            compare_dict = {
                'includeAddressFields': 'False',
                'path': 'patient search',
                'type': 'fhir_auth_pre_fetch',
            }
            remove_list = [
                'start_time',
                'uuid'
            ]
            hasvalue_list = [
                'start_time',
                'uuid'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            # fhir_auth_post_fetch
            log_entry_dict = json.loads(log_entries[1])
            compare_dict = {
                'code': 200,
                'includeAddressFields': 'False',
                'path': 'patient search',
                'type': 'fhir_auth_post_fetch',
            }
            remove_list = [
                'elapsed',
                'size',
                'start_time',
                'uuid'
            ]
            hasvalue_list = [
                'elapsed',
                'size',
                'start_time',
                'uuid'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            match_fhir_id_log_content = self.get_log_content('audit.authenticate.match_fhir_id')
            log_entries = match_fhir_id_log_content.splitlines()
            self.assertGreater(len(log_entries), 0)
            # fhir.server.authentication.match_fhir_id
            log_entry_dict = json.loads(log_entries[0])
            compare_dict = {
                'fhir_id': '-20140000008325',
                'hash_lookup_mesg': 'FOUND beneficiary via mbi_hash',
                'hash_lookup_type': 'M',
                'match_found': True,
                'type': 'fhir.server.authentication.match_fhir_id'
            }
            remove_list = [
                'auth_app_id',
                'auth_app_name',
                'auth_client_id',
                'auth_pkce_method',
                'hicn_hash',
                'mbi_hash',
                'auth_uuid'
            ]
            hasvalue_list = [
                'hicn_hash',
                'mbi_hash'
            ]
            self.assert_log_entry_valid(log_entry_dict, compare_dict, remove_list, hasvalue_list)

            hhs_oauth_server_log_content = self.get_log_content('audit.hhs_oauth_server.request_logging')
            log_entries = hhs_oauth_server_log_content.splitlines()
            self.assertGreater(len(log_entries), 0)
            # hhs oauth server request logging
            log_entry_dict = json.loads(log_entries[0])

            log_flds = ["start_time", "end_time", "request_uuid",
                        "path", "response_code", "size", "location",
                        "app_name", "app_id", "dev_id", "dev_name",
                        "access_token_hash", "ip_addr", "auth_crosswalk_action",
                        "user", "fhir_id"]
            keys = log_entry_dict.keys()
            for f in log_flds:
                self.assertTrue(f in keys)

    def test_creation_on_approval_token_logger(self):
        # copy and adapted to test token logger
        redirect_uri = 'http://localhost'
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        self.client.login(username='anna', password='123456')

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
        }
        response = self.client.get('/v1/o/authorize', data=payload)
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(response['Location'], data=payload)
        self.assertEqual(response.status_code, 302)
        # assert token logger record works by assert some top level fields
        token_log_content = self.get_log_content('audit.authorization.token')
        self.assertIsNotNone(token_log_content)

        # Validate Authorization entry
        token_log_dict = json.loads(token_log_content)
        """
        Example token_log_dict:
        {   'access_token_delete_cnt': 0,
            'allow': True,
            'application': {'id': 1, 'name': 'an app'},
            'auth_app_id': '1',
            'auth_app_name': 'an app',
            'auth_client_id': 'gHTJido7WsWvxfIjTAda9gcGSqSVjeSt65MZt5aS',
            'auth_pkce_method': None,
            'auth_require_demographic_scopes': 'True',
            'auth_share_demographic_scopes': '',
            'auth_status': 'OK',
            'auth_status_code': None,
            'auth_uuid': '7437e6bb-d97e-4ceb-9844-0603b2717100',
            'data_access_grant_delete_cnt': 0,
            'refresh_token_delete_cnt': 0,
            'scopes': 'capability-a',
            'share_demographic_scopes': '',
            'type': 'Authorization',
            'user': {   'crosswalk': {   'fhir_id': '-20140000008325',
                                         'id': 1,
                                         'user_hicn_hash': '96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7',
                                         'user_id_type': 'H',
                                         'user_mbi_hash': '98765432137efea543f4f370f96f1dbf01c3e3129041dba3ea43675987654321'},
                        'id': 1,
                        'username': 'anna'}}
        """
        compare_dict = {
            'access_token_delete_cnt': 0,
            'allow': True,
            'application': {'id': 1, 'name': 'an app'},
            'auth_app_id': '1',
            'auth_app_name': 'an app',
            'auth_require_demographic_scopes': 'True',
            'auth_share_demographic_scopes': '',
            'auth_status': 'OK',
            'data_access_grant_delete_cnt': 0,
            'refresh_token_delete_cnt': 0,
            'scopes': 'capability-a',
            'share_demographic_scopes': '',
            'type': 'Authorization'
        }
        remove_list = [
            'auth_client_id',
            'auth_pkce_method',
            'auth_status_code',
            'auth_uuid',
            'user',
        ]
        hasvalue_list = [
            'auth_uuid',
            'auth_client_id',
        ]
        self.assert_log_entry_valid(token_log_dict, compare_dict, remove_list, hasvalue_list)

        # Copy user to compare seperately, since there is an issue with nested dicts
        user_log_dict = token_log_dict['user']
        compare_dict = {
            'crosswalk': {'fhir_id': '-20140000008325',
                          'id': 1,
                          'user_hicn_hash': '96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7',
                          'user_id_type': 'H',
                          'user_mbi_hash': '98765432137efea543f4f370f96f1dbf01c3e3129041dba3ea43675987654321'},
            'id': 1,
            'username': 'anna'}
        self.assert_log_entry_valid(user_log_dict, compare_dict, [], [])
