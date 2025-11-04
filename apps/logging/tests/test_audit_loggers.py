import re
import json
import jsonschema
import requests

import apps.logging.request_logger as logging

from django.conf import settings
from django.urls import reverse
from django.test.client import Client
from django.contrib.auth.models import Group
from django.http import HttpRequest

from httmock import all_requests, HTTMock, urlmatch
from jsonschema import validate
from oauth2_provider.models import get_access_token_model
from rest_framework import status

from apps.dot_ext.models import Application
from apps.logging.utils import redirect_loggers, get_log_content, cleanup_logger
from apps.mymedicare_cb.views import generate_nonce
from apps.mymedicare_cb.models import AnonUserState
from apps.mymedicare_cb.tests.mock_url_responses_slsx import MockUrlSLSxResponses
from apps.mymedicare_cb.tests.responses import patient_response
from apps.test import BaseApiTest
from apps.constants import Versions
from .audit_logger_schemas import (
    ACCESS_TOKEN_AUTHORIZED_LOG_SCHEMA,
    AUTHENTICATION_START_LOG_SCHEMA,
    AUTHENTICATION_SUCCESS_LOG_SCHEMA,
    AUTHORIZATION_LOG_SCHEMA,
    FHIR_AUTH_POST_FETCH_LOG_SCHEMA,
    FHIR_AUTH_PRE_FETCH_LOG_SCHEMA,
    get_post_fetch_fhir_log_entry_schema,
    get_pre_fetch_fhir_log_entry_schema,
    MATCH_FHIR_ID_LOG_SCHEMA,
    MYMEDICARE_CB_CREATE_BENE_LOG_SCHEMA,
    MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA,
    REQUEST_RESPONSE_MIDDLEWARE_LOG_SCHEMA,
    REQUEST_PARTIAL_LOG_REC_SCHEMA,
    SLSX_TOKEN_LOG_SCHEMA,
    SLSX_USERINFO_LOG_SCHEMA,
)

from hhs_oauth_server.settings.base import MOCK_FHIR_ENDPOINT_HOSTNAME

FHIR_ID_V2 = settings.DEFAULT_SAMPLE_FHIR_ID_V2
FHIR_ID_V3 = settings.DEFAULT_SAMPLE_FHIR_ID_V3


class HTTMockWithResponseHook(HTTMock):
    def intercept(self, request, **kwargs):
        response = super().intercept(request, **kwargs)
        # process hooks - we only have response hook for now
        self.dispatch_hook('response', request.hooks, response, **kwargs)
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
        self._create_capability(
            'patient',
            [
                ['GET', r'\/v1\/fhir\/Patient\/\-\d+'],
                ['GET', '/v1/fhir/Patient'],
                ['GET', r'\/v2\/fhir\/Patient\/\-\d+'],
                ['GET', '/v2/fhir/Patient'],
                ['GET', r'\/v3\/fhir\/Patient\/\-\d+'],
                ['GET', '/v3/fhir/Patient'],
            ],
        )
        # Setup the RequestFactory
        self.client = Client()
        self.logger_registry = redirect_loggers()
        self.mock_response = MockUrlSLSxResponses()

    def tearDown(self):
        cleanup_logger(self.logger_registry)

    def _validateJsonSchema(self, schema, content):
        try:
            validate(instance=content, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            # Show error info for debugging
            print('jsonschema.exceptions.ValidationError: ', e)
            return False
        return True

    def test_fhir_events_logging(self):
        self._fhir_events_logging(Versions.V1)

    def test_fhir_events_logging_v2(self):
        self._fhir_events_logging(Versions.V2)

    def test_fhir_events_logging_v3(self):
        self._fhir_events_logging(Versions.V3)

    def _fhir_events_logging(self, version=1):
        if version == Versions.V3:
            first_access_token = self.create_token('John', 'Smith', fhir_id_v3=FHIR_ID_V3)
        else:
            first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)
        AccessToken = get_access_token_model()
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Coverage.read patient/Patient.read patient/ExplanationOfBenefit.read'
        ac.save()

        @all_requests
        def catchall(url, req):
            fhir_log_content = get_log_content(self.logger_registry, logging.AUDIT_DATA_FHIR_LOGGER)
            self.assertIsNotNone(fhir_log_content)

            # Validate FHIR Patient response
            log_entry_dict = json.loads(fhir_log_content)
            self.assertTrue(
                self._validateJsonSchema(
                    get_pre_fetch_fhir_log_entry_schema(version), log_entry_dict
                )
            )

            return {
                'status_code': status.HTTP_200_OK,
                # TODO replace this with true backend response, this has been post proccessed
                'content': patient_response,
            }
        reverse_url = 'bb_oauth_fhir_patient_search'
        if version == Versions.V2:
            reverse_url += '_v2'
        elif version == Versions.V3:
            reverse_url += '_v3'

        with HTTMock(catchall):
            self.client.get(
                reverse(reverse_url),
                {'count': 5, 'hello': 'world'},
                Authorization='Bearer %s' % (first_access_token),
            )

            # fhir_log_content, token_log_content
            # check fhir log content
            fhir_log_content = get_log_content(self.logger_registry, logging.AUDIT_DATA_FHIR_LOGGER)
            self.assertIsNotNone(fhir_log_content)
            log_entries = fhir_log_content.splitlines()

            # Validate fhir_pre_fetch entry
            self.assertTrue(
                self._validateJsonSchema(
                    get_pre_fetch_fhir_log_entry_schema(version), json.loads(log_entries[0])
                )
            )

            # Validate fhir_post_fetch entry
            self.assertTrue(
                self._validateJsonSchema(
                    get_post_fetch_fhir_log_entry_schema(version), json.loads(log_entries[1])
                )
            )

            # Validate AccessToken entry
            token_log_content = get_log_content(self.logger_registry, logging.AUDIT_AUTHZ_TOKEN_LOGGER)
            self.assertIsNotNone(token_log_content)
            log_entries = token_log_content.splitlines()

            self.assertTrue(
                self._validateJsonSchema(
                    ACCESS_TOKEN_AUTHORIZED_LOG_SCHEMA, json.loads(log_entries[0])
                )
            )

    def test_callback_url_success_slsx_logger(self):
        self._callback_url_success_slsx_logger(1)

    def test_callback_url_success_slsx_logger_v2(self):
        self._callback_url_success_slsx_logger(2)

    def _callback_url_success_slsx_logger(self, version=1):
        # copy and adapted for SLSx logger test
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri='http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test',
        )

        # mock fhir user info endpoint
        @urlmatch(
            netloc=MOCK_FHIR_ENDPOINT_HOSTNAME,
            path=r'/v[123]/fhir/Patient/',
        )
        def fhir_patient_info_mock(url, request):
            return {
                'status_code': status.HTTP_200_OK,
                'content': patient_response,
            }

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        with HTTMockWithResponseHook(
            self.mock_response.slsx_token_mock,
            self.mock_response.slsx_user_info_mock,
            self.mock_response.slsx_signout_ok_mock,
            fhir_patient_info_mock,
            catchall,
        ):
            s = self.client.session
            s.update(
                {
                    'auth_uuid': '84b4afdc-d85d-4ea4-b44c-7bde77634429',
                    'auth_app_id': '2',
                    'version': version,
                    'auth_app_name': 'TestApp-001',
                    'auth_client_id': 'uouIr1mnblrv3z0PJHgmeHiYQmGVgmk5DZPDNfop',
                }
            )
            s.save()

            self.client.get(
                self.callback_url,
                data={'req_token': 'xxxx-request-token-xxxx', 'relay': state},
            )

            slsx_log_content = get_log_content(self.logger_registry, logging.AUDIT_AUTHZ_SLS_LOGGER)

            quoted_strings = re.findall('{[^{}]+}', slsx_log_content)
            self.assertEqual(len(quoted_strings), 2)

            # Validate token response
            self.assertTrue(
                self._validateJsonSchema(SLSX_TOKEN_LOG_SCHEMA, json.loads(quoted_strings[0]))
            )

            # Validate userinfo response
            slsx_userinfo_dict = json.loads(quoted_strings[1])
            self.assertTrue(
                self._validateJsonSchema(SLSX_USERINFO_LOG_SCHEMA, slsx_userinfo_dict)
            )

            authn_sls_log_content = get_log_content(self.logger_registry, logging.AUDIT_AUTHN_SLS_LOGGER)
            log_entries = authn_sls_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)

            # Validate Authentication:start entry
            self.assertTrue(
                self._validateJsonSchema(
                    AUTHENTICATION_START_LOG_SCHEMA, json.loads(log_entries[0])
                )
            )

            # Validate Authentication:success entry
            self.assertTrue(
                self._validateJsonSchema(
                    AUTHENTICATION_SUCCESS_LOG_SCHEMA, json.loads(log_entries[1])
                )
            )

            mymedicare_cb_log_content = get_log_content(self.logger_registry, logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER)
            log_entries = mymedicare_cb_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)

            # Validate mymedicare_cb:create_beneficiary_record entry
            self.assertTrue(
                self._validateJsonSchema(
                    MYMEDICARE_CB_CREATE_BENE_LOG_SCHEMA, json.loads(log_entries[0])
                )
            )

            # Validate mymedicare_cb:get_and_update_user entry
            self.assertTrue(
                self._validateJsonSchema(
                    MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA, json.loads(log_entries[1])
                )
            )

            fhir_log_content = get_log_content(self.logger_registry, logging.AUDIT_DATA_FHIR_LOGGER)
            log_entries = fhir_log_content.splitlines()
            self.assertEqual(len(log_entries), 2)

            # Validate fhir_auth_pre_fetch entry
            self.assertTrue(
                self._validateJsonSchema(FHIR_AUTH_PRE_FETCH_LOG_SCHEMA, json.loads(log_entries[0]))
            )

            # Validate fhir_auth_post_fetch entry
            self.assertTrue(
                self._validateJsonSchema(
                    FHIR_AUTH_POST_FETCH_LOG_SCHEMA, json.loads(log_entries[1])
                )
            )

            match_fhir_id_log_content = get_log_content(self.logger_registry, logging.AUDIT_AUTHN_MATCH_FHIR_ID_LOGGER)

            log_entries = match_fhir_id_log_content.splitlines()
            self.assertGreater(len(log_entries), 0)

            # Validate fhir.server.authentication.match_fhir_id entry
            self.assertTrue(
                self._validateJsonSchema(MATCH_FHIR_ID_LOG_SCHEMA, json.loads(log_entries[0]))
            )

            hhs_oauth_server_log_content = get_log_content(self.logger_registry, logging.AUDIT_HHS_AUTH_SERVER_REQ_LOGGER)

            log_entries = hhs_oauth_server_log_content.splitlines()
            self.assertGreater(len(log_entries), 0)

            # Validate hhs_oauth_server request/response custom middleware log entry
            self.assertTrue(
                self._validateJsonSchema(
                    REQUEST_RESPONSE_MIDDLEWARE_LOG_SCHEMA, json.loads(log_entries[0])
                )
            )

    def test_callback_url_slsx_tkn_error_logger(self):
        self._callback_url_slsx_tkn_error_logger(1)

    def test_callback_url_slsx_tkn_error_logger_v2(self):
        self._callback_url_slsx_tkn_error_logger(2)

    def _callback_url_slsx_tkn_error_logger(self, version):
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri='http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test',
        )

        # mock fhir user info endpoint
        @urlmatch(
            netloc=MOCK_FHIR_ENDPOINT_HOSTNAME,
            path=r'/v[123]/fhir/Patient/',
        )
        def fhir_patient_info_mock(url, request):
            return {
                'status_code': 200,
                'content': patient_response,
            }

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        with HTTMockWithResponseHook(
            self.mock_response.slsx_token_non_json_response_mock,
            self.mock_response.slsx_user_info_mock,
            fhir_patient_info_mock,
            catchall,
        ):
            s = self.client.session
            s.update(
                {
                    'auth_uuid': '84b4afdc-d85d-4ea4-b44c-7bde77634429',
                    'auth_app_id': '2',
                    'version': version,
                    'auth_app_name': 'TestApp-001',
                    'auth_client_id': 'uouIr1mnblrv3z0PJHgmeHiYQmGVgmk5DZPDNfop',
                }
            )
            s.save()

            try:
                self.client.get(
                    self.callback_url,
                    data={'req_token': 'xxxx-request-token-xxxx', 'relay': state},
                )
                self.fail('HTTP Error 403 expected.')
            except requests.exceptions.HTTPError as err:
                self.assertEqual(err.response.status_code, status.HTTP_403_FORBIDDEN)

            slsx_log_content = get_log_content(self.logger_registry, logging.AUDIT_AUTHZ_SLS_LOGGER)
            quoted_strings = re.findall('{[^{}]+}', slsx_log_content)

            self.assertEqual(len(quoted_strings), 1)

            log_entry_dict = json.loads(quoted_strings[0])
            self.assertIsNotNone(log_entry_dict.get('message'))
            self.assertEqual(
                log_entry_dict.get('message'),
                'JSONDecodeError thrown when parsing response text.',
            )

    def test_callback_url_slsx_userinfo_error_logger(self):
        self._callback_url_slsx_userinfo_error_logger(1)

    def test_callback_url_slsx_userinfo_error_logger_v2(self):
        self._callback_url_slsx_userinfo_error_logger(2)

    def _callback_url_slsx_userinfo_error_logger(self, version=1):
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri='http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test',
        )

        # mock fhir user info endpoint
        @urlmatch(
            netloc=MOCK_FHIR_ENDPOINT_HOSTNAME,
            path=r'/v[123]/fhir/Patient/',
        )
        def fhir_patient_info_mock(url, request):
            return {
                'status_code': 200,
                'content': patient_response,
            }

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        with HTTMockWithResponseHook(
            self.mock_response.slsx_token_mock,
            self.mock_response.slsx_user_info_non_json_response_mock,
            fhir_patient_info_mock,
            catchall,
        ):
            s = self.client.session
            s.update(
                {
                    'auth_uuid': '84b4afdc-d85d-4ea4-b44c-7bde77634429',
                    'auth_app_id': '2',
                    'version': version,
                    'auth_app_name': 'TestApp-001',
                    'auth_client_id': 'uouIr1mnblrv3z0PJHgmeHiYQmGVgmk5DZPDNfop',
                }
            )
            s.save()

            try:
                self.client.get(
                    self.callback_url,
                    data={'req_token': 'xxxx-request-token-xxxx', 'relay': state},
                )
                self.fail('HTTP Error 403 expected.')
            except requests.exceptions.HTTPError as err:
                self.assertEqual(err.response.status_code, status.HTTP_403_FORBIDDEN)

            slsx_log_content = get_log_content(self.logger_registry, logging.AUDIT_AUTHZ_SLS_LOGGER)
            quoted_strings = re.findall('{[^{}]+}', slsx_log_content)

            self.assertEqual(len(quoted_strings), 2)

            log_entry_dict = json.loads(quoted_strings[1])
            self.assertIsNotNone(log_entry_dict.get('message'))
            self.assertEqual(
                log_entry_dict.get('message'),
                'JSONDecodeError thrown when parsing response text.',
            )

    def test_creation_on_approval_token_logger(self):
        self._creation_on_approval_token_logger(1)

    def test_creation_on_approval_token_logger_v2(self):
        self._creation_on_approval_token_logger(2)

    def _creation_on_approval_token_logger(self, version=1):
        # copy and adapted to test token logger
        redirect_uri = 'http://localhost'
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri,
        )
        application.scope.add(capability_a, capability_b)
        api_ver = 'v1'
        if version == 2:
            api_ver = 'v2'
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
        }
        response = self.client.get('/{}/o/authorize'.format(api_ver), data=payload)
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
            'state': '0123456789abcdef',
        }
        response = self.client.post(response['Location'], data=payload)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # assert token logger record works by assert some top level fields
        token_log_content = get_log_content(self.logger_registry, logging.AUDIT_AUTHZ_TOKEN_LOGGER)
        self.assertIsNotNone(token_log_content)

        # Validate Authorization entry
        token_log_dict = json.loads(token_log_content)
        self.assertTrue(
            self._validateJsonSchema(AUTHORIZATION_LOG_SCHEMA, token_log_dict)
        )

    def test_request_logger_app_not_exist(self):
        self._request_logger_app_not_exist(1)

    def test_request_logger_app_not_exist_v2(self):
        self._request_logger_app_not_exist(2)

    def _request_logger_app_not_exist(self, version=1):
        # copy and adapted to test token logger
        redirect_uri = 'http://localhost'
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri,
        )

        application.scope.add(capability_a, capability_b)

        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')

        non_exist_client_id = application.client_id + '_non_exist'

        payload = {
            'client_id': non_exist_client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
        }

        response = self.client.get(f'/v{version}/o/authorize/', data=payload)

        self.assertNotEqual(response.status_code, 500)
        # assert request logger record exist and app name, app id has expected value ''
        request_log_content = get_log_content(self.logger_registry, logging.AUDIT_HHS_AUTH_SERVER_REQ_LOGGER)
        self.assertIsNotNone(request_log_content)
        json_rec = json.loads(request_log_content)
        self.assertTrue(self._validateJsonSchema(REQUEST_PARTIAL_LOG_REC_SCHEMA, json_rec))
        self.assertEqual(json_rec.get('req_qparam_client_id'), non_exist_client_id)
        self.assertEqual(json_rec.get('req_app_name'), '')
        self.assertEqual(json_rec.get('req_app_id'), '')

    def test_request_logger_data_facilitator_end_user(self):
        self._request_logger_data_facilitator_end_user(1)

    def test_request_logger_data_facilitator_end_user_v2(self):
        self._request_logger_data_facilitator_end_user(2)

    def _request_logger_data_facilitator_end_user(self, version=1):
        redirect_uri = 'http://localhost'
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri,
        )

        application.scope.add(capability_a, capability_b)

        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')

        payload = {
            'client_id': application.id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
        }

        headers = {'DATA-END-USER': 'End User App'}

        response = self.client.get(f'/v{version}/o/authorize/', data=payload, headers=headers)

        self.assertNotEqual(response.status_code, 500)
        # assert request logger record exist and app name, app id has expected value ''
        request_log_content = get_log_content(self.logger_registry, logging.AUDIT_HHS_AUTH_SERVER_REQ_LOGGER)
        self.assertIsNotNone(request_log_content)
        json_rec = json.loads(request_log_content)
        self.assertEqual(json_rec.get('data_facilitator_end_user'), 'End User App')

    def test_auth_flow_lang_logger(self, version=1):
        # copy and adapted to test auth flow logger
        redirect_uri = 'http://localhost'
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri,
        )
        application.scope.add(capability_a, capability_b)
        # No user already logged in so that the authorization flow goes through
        # dispatch

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'lang': 'es',
        }

        response = self.client.get('/v2/o/authorize', data=payload)
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
            'state': '0123456789abcdef',
        }
        response = self.client.post(response['Location'], data=payload)
        request_log_content = get_log_content(self.logger_registry,
                                              logging.AUDIT_HHS_AUTH_SERVER_REQ_LOGGER)
        self.assertIsNotNone(request_log_content)
        quoted_strings = re.findall('{[^{}]+}', request_log_content)
        self.assertEqual(len(quoted_strings), 2)

        second_stanza_dict = json.loads(quoted_strings[1])
        self.assertEqual(second_stanza_dict.get('auth_language'), 'es')
