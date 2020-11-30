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

    def tearDown(self):
        # do not close stream, only close channel
        # self.log_buffer_sls.close()
        self.channel_sls.close()
        # self.log_buffer_token.close()
        self.channel_token.close()
        # self.log_buffer_fhir.close()
        self.channel_fhir.close()

    def X_test_fhir_events_logging(self):
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
            # check fhir log content
            fhir_log_content = self.log_buffer_fhir.getvalue()
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

    def X_test_callback_url_success_sls_logger(self):
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
            sls_log_content = self.log_buffer_sls.getvalue()
            quoted_strings = re.findall("{[^{}]+}", sls_log_content)
            self.assertEqual(len(quoted_strings), 2)
            sls_token_dict = json.loads(quoted_strings[0])
            sls_userinfo_dict = json.loads(quoted_strings[1])
            self.assertEqual(sls_token_dict["type"], "SLS_token")
            self.assertIsNotNone(sls_token_dict["access_token"])

            self.assertEqual(sls_userinfo_dict["type"], "SLS_userinfo")
            self.assertEqual(sls_userinfo_dict["sub"], "00112233-4455-6677-8899-aabbccddeeff")

    def test_creation_on_approval_token_logger(self):
        # copy and adapted o=to test token logger
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
        token_log_content = self.log_buffer_token.getvalue()
        self.assertIsNotNone(token_log_content)
        token_log_record = json.loads(token_log_content)
        self.assertEqual(token_log_record["type"], "Authorization")
        self.assertIsNotNone(token_log_record["auth_uuid"])
        self.assertEqual(token_log_record["auth_app_name"], "an app")
        self.assertEqual(token_log_record["auth_status"], "OK")
        self.assertIsNotNone(token_log_record["user"])
        self.assertIsNotNone(token_log_record["application"])
