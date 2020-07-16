import logging
import re

from io import StringIO
from django.urls import reverse
from apps.mymedicare_cb.views import generate_nonce
from apps.mymedicare_cb.models import AnonUserState
from apps.mymedicare_cb.tests.responses import patient_response
from httmock import urlmatch, all_requests, HTTMock
from django.contrib.auth.models import Group
from apps.test import BaseApiTest

from oauth2_provider.models import (
    get_access_token_model,
    get_refresh_token_model,
)

AccessToken = get_access_token_model()
RefreshToken = get_refresh_token_model()


# paste from python requests sessions
def dispatch_hook(key, hooks, hook_data, **kwargs):
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


class HTTMockRespHook(HTTMock):
    def intercept(self, request, **kwargs):
        resp = HTTMock.intercept(self, request, **kwargs)
        if request.hooks is not None:
            return dispatch_hook('response', request.hooks, resp, **kwargs)
        return resp


class SignalBasedRespHookLoggingTest(BaseApiTest):
    """
    Test logging for MyMedicare login and SLS Callback
    """
    def setUp(self):
        self.callback_url = reverse('mymedicare-sls-callback')
        self.login_url = reverse('mymedicare-login')
        Group.objects.create(name='BlueButton')

        self.token_logger = logging.getLogger('audit.authorization.token')
        self.token_logger.setLevel(logging.INFO)
        self.token_stream = StringIO()
        self.token_ch = logging.StreamHandler(self.token_stream)
        self.token_ch.setLevel(logging.INFO)
        self.token_logger.addHandler(self.token_ch)
        for h in self.token_logger.handlers:
            self.token_logger.removeHandler(h)
        self.token_logger.addHandler(self.token_ch)
        self.sls_logger = logging.getLogger('audit.authorization.sls')
        self.sls_logger.setLevel(logging.INFO)
        self.sls_stream = StringIO()
        self.sls_ch = logging.StreamHandler(self.sls_stream)
        self.sls_ch.setLevel(logging.INFO)
        self.sls_logger.addHandler(self.sls_ch)
        for h in self.sls_logger.handlers:
            self.sls_logger.removeHandler(h)
        self.sls_logger.addHandler(self.sls_ch)
        self.fhir_logger = logging.getLogger('audit.data.fhir')
        self.fhir_logger.setLevel(logging.INFO)
        self.fhir_stream = StringIO()
        self.fhir_ch = logging.StreamHandler(self.fhir_stream)
        self.fhir_ch.setLevel(logging.INFO)
        self.fhir_logger.addHandler(self.fhir_ch)
        for h in self.fhir_logger.handlers:
            self.fhir_logger.removeHandler(h)
        self.fhir_logger.addHandler(self.fhir_ch)

    def tearDown(self):
        # tear down token logger
        self.token_logger.removeHandler(self.token_ch)
        del self.token_logger, self.token_ch, self.token_stream
        # tear down sls logger
        self.sls_logger.removeHandler(self.sls_ch)
        del self.sls_logger, self.sls_ch, self.sls_stream
        # tear down fhir logger
        self.fhir_logger.removeHandler(self.fhir_ch)
        del self.fhir_logger, self.fhir_ch, self.fhir_stream

    def test_callback_logging(self):
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

        with HTTMockRespHook(sls_token_mock,
                             sls_user_info_mock,
                             fhir_patient_info_mock,
                             catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})
            # assert http redirect
            self.assertEqual(response.status_code, 302)
            self.assertIn("client_id=test", response.url)
            self.assertIn("redirect_uri=test.com", response.url)
            # self.assertRedirects(response, "http://www.google.com", fetch_redirect_response=False)
            # assert login
            self.assertNotIn('_auth_user_id', self.client.session)
            log_entries = self.sls_stream.getvalue()
            log_lines = log_entries.splitlines()
            sls_token_pattern = '.*type.*:.*SLS_token.*'
            sls_userinfo_pattern = '.*type.*:.*SLS_userinfo.*'
            has_token = False
            has_userinfo = False
            for line in log_lines:
                if re.match(sls_token_pattern, line) is not None:
                    has_token = True
                if re.match(sls_userinfo_pattern, line) is not None:
                    has_userinfo = True
            self.assertTrue(has_token, 'Expect "type" : "SLS_token" ... in log record, but not found.')
            self.assertTrue(has_userinfo, 'Expect "type" : "SLS_userinfo" ... in log record, but not found.')
