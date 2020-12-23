import logging
import io
import re
import json
from django.urls import reverse
from django.test.client import Client
from django.contrib.auth.models import Group
from httmock import all_requests, HTTMock, urlmatch

from apps.dot_ext.models import Application
from apps.test import BaseApiTest
from apps.mymedicare_cb.views import generate_nonce
from apps.mymedicare_cb.models import AnonUserState
from apps.mymedicare_cb.tests.responses import patient_response

token_logger = logging.getLogger('audit.authorization.token')
sls_logger = logging.getLogger('audit.authorization.sls')
fhir_logger = logging.getLogger('audit.data.fhir')
authenticate_logger = logging.getLogger('audit.authenticate.sls')
mymedicare_cb_logger = logging.getLogger('audit.authenticate.mymedicare_cb')
match_fhir_id_logger = logging.getLogger('audit.authenticate.match_fhir_id')
hhs_oauth_server_request_logger = logging.getLogger('audit.hhs_oauth_server.request_logging')


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
        # capture sls logging records
        self.log_buffer_sls = io.StringIO()
        self.channel_sls = logging.StreamHandler(self.log_buffer_sls)
        self.channel_sls.setLevel(logging.INFO)
        sls_logger.setLevel(logging.INFO)
        sls_logger.addHandler(self.channel_sls)
        # capture token logging records
        self.log_buffer_token = io.StringIO()
        self.channel_token = logging.StreamHandler(self.log_buffer_token)
        self.channel_token.setLevel(logging.INFO)
        token_logger.setLevel(logging.INFO)
        token_logger.addHandler(self.channel_token)
        # capture fhir data logging records
        self.log_buffer_fhir = io.StringIO()
        self.channel_fhir = logging.StreamHandler(self.log_buffer_fhir)
        self.channel_fhir.setLevel(logging.INFO)
        fhir_logger.setLevel(logging.INFO)
        fhir_logger.addHandler(self.channel_fhir)
        # capture authenticate_logger logging records
        self.log_buffer_authn_sls = io.StringIO()
        self.channel_authn_sls = logging.StreamHandler(self.log_buffer_authn_sls)
        self.channel_authn_sls.setLevel(logging.INFO)
        authenticate_logger.setLevel(logging.INFO)
        authenticate_logger.addHandler(self.channel_authn_sls)
        # capture mymedicare_cb_logger logging records
        self.log_buffer_mymedicare_cb = io.StringIO()
        self.channel_mymedicare_cb = logging.StreamHandler(self.log_buffer_mymedicare_cb)
        self.channel_mymedicare_cb.setLevel(logging.INFO)
        mymedicare_cb_logger.setLevel(logging.INFO)
        mymedicare_cb_logger.addHandler(self.channel_mymedicare_cb)
        # capture match_fhir_id_logger logging records
        self.log_buffer_match_fhir_id = io.StringIO()
        self.channel_match_fhir_id = logging.StreamHandler(self.log_buffer_match_fhir_id)
        self.channel_match_fhir_id.setLevel(logging.INFO)
        match_fhir_id_logger.setLevel(logging.INFO)
        match_fhir_id_logger.addHandler(self.channel_match_fhir_id)
        # capture match_fhir_id_logger logging records
        self.log_buffer_hhs_oauth_server_request = io.StringIO()
        self.channel_hhs_oauth_server_request = logging.StreamHandler(self.log_buffer_hhs_oauth_server_request)
        self.channel_hhs_oauth_server_request.setLevel(logging.INFO)
        hhs_oauth_server_request_logger.setLevel(logging.INFO)
        hhs_oauth_server_request_logger.addHandler(self.channel_hhs_oauth_server_request)

    def tearDown(self):
        # do not close stream, only close channel
        # self.log_buffer_sls.close()
        self.channel_sls.close()
        # self.log_buffer_token.close()
        self.channel_token.close()
        # self.log_buffer_fhir.close()
        self.channel_fhir.close()
        # close authenticate sls logger (channel)
        self.channel_authn_sls.close()
        # close mymedicare_cb logger (channel)
        self.channel_mymedicare_cb.close()
        # close match_fhir_id logger (channel)
        self.channel_match_fhir_id.close()
        # close channel_hhs_oauth_server_request logger (channel)
        self.channel_hhs_oauth_server_request.close()

    def collect_logs(self):
        return {
            "token_log_content": self.log_buffer_token.getvalue(),
            "fhir_log_content": self.log_buffer_fhir.getvalue(),
            "sls_log_content": self.log_buffer_sls.getvalue(),
            "mymedicare_cb_log_content": self.log_buffer_mymedicare_cb.getvalue(),
            "authn_sls_log_content": self.log_buffer_authn_sls.getvalue(),
            "match_fhir_id_log_content": self.log_buffer_match_fhir_id.getvalue(),
            "hhs_oauth_server_log_content": self.log_buffer_hhs_oauth_server_request.getvalue(),
        }

    def test_fhir_events_logging(self):
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            fhir_log_content = self.log_buffer_fhir.getvalue()
            self.assertIsNotNone(fhir_log_content)
            log_entry_dict = json.loads(fhir_log_content)
            self.assertEqual(log_entry_dict["fhir_id"], "-20140000008325")
            self.assertEqual(log_entry_dict["user"], "patientId:-20140000008325")
            self.assertEqual(log_entry_dict["path"], "/v1/fhir/Patient")
            self.assertIsNotNone(log_entry_dict["application"])
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

            log_contents = self.collect_logs()
            # fhir_log_content, token_log_content
            # check fhir log content
            fhir_log_content = log_contents['fhir_log_content']
            self.assertIsNotNone(fhir_log_content)
            log_entries = fhir_log_content.splitlines()

            log_entry_dict = json.loads(log_entries[0])
            self.assertEqual(log_entry_dict["type"], "fhir_pre_fetch")
            self.assertEqual(log_entry_dict["fhir_id"], "-20140000008325")
            self.assertEqual(log_entry_dict["user"], "patientId:-20140000008325")
            self.assertEqual(log_entry_dict["path"], "/v1/fhir/Patient")
            self.assertIsNotNone(log_entry_dict["application"])

            log_entry_dict = json.loads(log_entries[1])
            self.assertEqual(log_entry_dict["type"], "fhir_post_fetch")
            self.assertEqual(log_entry_dict["fhir_id"], "-20140000008325")
            self.assertEqual(log_entry_dict["user"], "patientId:-20140000008325")
            self.assertEqual(log_entry_dict["path"], "/v1/fhir/Patient")
            self.assertIsNotNone(log_entry_dict["application"])
            # check token log content
            token_log_content = log_contents['token_log_content']
            self.assertIsNotNone(token_log_content)
            log_entries = token_log_content.splitlines()
            log_entry_dict = json.loads(log_entries[0])
            self.assertEqual(log_entry_dict["type"], "AccessToken")
            self.assertEqual(log_entry_dict["action"], "authorized")
            self.assertEqual(log_entry_dict["scopes"], "read write patient")
            self.assertIsNotNone(log_entry_dict["access_token"])
            self.assertIsNotNone(log_entry_dict["application"])

    def test_callback_url_success_sls_logger(self):
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

            log_contents = self.collect_logs()

            sls_log_content = log_contents['sls_log_content']

            quoted_strings = re.findall("{[^{}]+}", sls_log_content)
            self.assertEqual(len(quoted_strings), 2)
            sls_token_dict = json.loads(quoted_strings[0])
            sls_userinfo_dict = json.loads(quoted_strings[1])
            self.assertEqual(sls_token_dict["type"], "SLS_token")
            self.assertIsNotNone(sls_token_dict["access_token"])

            self.assertEqual(sls_userinfo_dict["type"], "SLS_userinfo")
            self.assertEqual(sls_userinfo_dict["sub"], "00112233-4455-6677-8899-aabbccddeeff")

            authn_sls_log_content = log_contents['authn_sls_log_content']
            log_entries = authn_sls_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)
            # Authentication:start
            log_entry_dict = json.loads(log_entries[0])
            self.assertEqual(log_entry_dict["type"], "Authentication:start")
            self.assertEqual(log_entry_dict["sls_status"], "OK")
            self.assertEqual(log_entry_dict["sub"], "00112233-4455-6677-8899-aabbccddeeff")
            self.assertIsNotNone(log_entry_dict["sls_mbi_format_valid"])
            self.assertIsNotNone(log_entry_dict["sls_mbi_format_msg"])
            self.assertIsNotNone(log_entry_dict["sls_mbi_format_synthetic"])
            self.assertIsNotNone(log_entry_dict["sls_hicn_hash"])
            self.assertIsNotNone(log_entry_dict["sls_mbi_hash"])
            # Authentication:success
            log_entry_dict = json.loads(log_entries[1])
            self.assertEqual(log_entry_dict["type"], "Authentication:success")
            self.assertEqual(log_entry_dict["sub"], "00112233-4455-6677-8899-aabbccddeeff")
            self.assertEqual(log_entry_dict["auth_crosswalk_action"], "C")
            self.assertIsNotNone(log_entry_dict["user"])

            mymedicare_cb_log_content = log_contents['mymedicare_cb_log_content']
            log_entries = mymedicare_cb_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)
            # mymedicare_cb:create_beneficiary_record
            log_entry_dict = json.loads(log_entries[0])
            self.assertEqual(log_entry_dict["type"], "mymedicare_cb:create_beneficiary_record")
            self.assertEqual(log_entry_dict["status"], "OK")
            self.assertEqual(log_entry_dict["username"], "00112233-4455-6677-8899-aabbccddeeff")
            self.assertEqual(log_entry_dict["fhir_id"], "-20140000008325")
            self.assertIsNotNone(log_entry_dict["user_mbi_hash"])
            self.assertIsNotNone(log_entry_dict["user_hicn_hash"])
            self.assertEqual(log_entry_dict["mesg"], "CREATE beneficiary record")

            # mymedicare_cb:get_and_update_user
            log_entry_dict = json.loads(log_entries[1])
            self.assertEqual(log_entry_dict["type"], "mymedicare_cb:get_and_update_user")
            self.assertEqual(log_entry_dict["status"], "OK")
            self.assertEqual(log_entry_dict["fhir_id"], "-20140000008325")
            self.assertEqual(log_entry_dict["hash_lookup_type"], "M")
            self.assertEqual(log_entry_dict["mesg"], "CREATE beneficiary record")
            self.assertIsNotNone(log_entry_dict["crosswalk"])
            self.assertIsNotNone(log_entry_dict["mbi_hash"])
            self.assertIsNotNone(log_entry_dict["hicn_hash"])

            fhir_log_content = log_contents['fhir_log_content']
            log_entries = fhir_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)
            # fhir_auth_pre_fetch
            log_entry_dict = json.loads(log_entries[0])
            self.assertEqual(log_entry_dict["type"], "fhir_auth_pre_fetch")
            self.assertEqual(log_entry_dict["includeAddressFields"], 'False')
            self.assertEqual(log_entry_dict["path"], "patient search")
            self.assertIsNotNone(log_entry_dict["uuid"])
            self.assertIsNotNone(log_entry_dict["start_time"])

            # fhir_auth_post_fetch
            log_entry_dict = json.loads(log_entries[1])
            self.assertEqual(log_entry_dict["type"], "fhir_auth_post_fetch")
            self.assertEqual(log_entry_dict["includeAddressFields"], 'False')
            self.assertEqual(log_entry_dict["path"], "patient search")
            self.assertEqual(log_entry_dict["code"], 200)
            self.assertIsNotNone(log_entry_dict["uuid"])
            self.assertIsNotNone(log_entry_dict["start_time"])
            self.assertIsNotNone(log_entry_dict["size"])
            self.assertIsNotNone(log_entry_dict["elapsed"])

            match_fhir_id_log_content = log_contents['match_fhir_id_log_content']
            log_entries = match_fhir_id_log_content.splitlines()
            self.assertGreater(len(log_entries), 0)
            # fhir.server.authentication.match_fhir_id
            log_entry_dict = json.loads(log_entries[0])
            self.assertEqual(log_entry_dict["type"], "fhir.server.authentication.match_fhir_id")
            self.assertEqual(log_entry_dict["fhir_id"], "-20140000008325")
            self.assertIsNotNone(log_entry_dict["mbi_hash"])
            self.assertIsNotNone(log_entry_dict["hicn_hash"])
            self.assertEqual(log_entry_dict["match_found"], True)
            self.assertEqual(log_entry_dict["hash_lookup_type"], "M")
            self.assertEqual(log_entry_dict["hash_lookup_mesg"], "FOUND beneficiary via mbi_hash")

            hhs_oauth_server_log_content = log_contents['hhs_oauth_server_log_content']
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
        log_contents = self.collect_logs()
        token_log_content = log_contents['token_log_content']
        self.assertIsNotNone(token_log_content)
        token_log_record = json.loads(token_log_content)
        self.assertEqual(token_log_record["type"], "Authorization")
        self.assertIsNotNone(token_log_record["auth_uuid"])
        self.assertEqual(token_log_record["auth_app_name"], "an app")
        self.assertEqual(token_log_record["auth_status"], "OK")
        self.assertIsNotNone(token_log_record["user"])
        self.assertIsNotNone(token_log_record["application"])
