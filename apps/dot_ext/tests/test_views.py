import json
import base64
from django.conf import settings
from django.urls import reverse
from httmock import HTTMock, urlmatch
from oauth2_provider.compat import parse_qs, urlparse
from oauth2_provider.models import AccessToken, RefreshToken
from rest_framework.test import APIClient
from waffle.testutils import override_switch
from apps.authorization.models import DataAccessGrant, ArchivedDataAccessGrant
from apps.dot_ext.models import ArchivedToken
from apps.fhir.server.tests.mock_fhir_responses import mock_fhir_responses

from apps.test import BaseApiTest
from ..models import Application
from .demographic_scopes_test_cases import (VIEW_OAUTH2_SCOPES_TEST_CASES,
                                            SCOPES_TO_URL_BASE_PATH)


class TestApplicationUpdateView(BaseApiTest):
    def test_update_form_show(self):
        """
        """
        read_group = self._create_group('read')
        self._create_capability('Read-Scope', [], read_group)
        write_group = self._create_group('write')
        self._create_capability('Write-Scope', [], write_group)
        # create user and add it to the read group
        user = self._create_user('john', '123456')
        user.groups.add(read_group)
        # create an application
        app = self._create_application('john_app', user=user)
        # render the edit view for the app
        self.client.login(username=user.username, password='123456')
        uri = reverse('oauth2_provider:update', args=[app.pk])
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)


class TestAuthorizationView(BaseApiTest):
    fixtures = ['scopes.json']

    MOCK_FHIR_URL = "fhir.backend.bluebutton.hhsdevcloud.us"
    MOCK_FHIR_PATIENT_READVIEW_PATH = r'/v1/fhir/Patient/[-]?\d+[/]?'
    MOCK_FHIR_PATIENT_SEARCHVIEW_PATH = r'/v1/fhir/Patient[/]?'
    MOCK_FHIR_EOB_PATH = r'/v1/fhir/ExplanationOfBenefit[/]?'
    MOCK_FHIR_COVERAGE_PATH = r'/v1/fhir/Coverage[/]?'

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_PATIENT_READVIEW_PATH)
    def fhir_request_patient_readview_success_mock(self, url, request):
        # Return successful respose for Patient FHIR requests
        return mock_fhir_responses['success_patient_readview']

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_PATIENT_SEARCHVIEW_PATH)
    def fhir_request_patient_searchview_success_mock(self, url, request):
        # Return successful respose for Patient FHIR requests
        return mock_fhir_responses['success_patient_searchview']

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_EOB_PATH)
    def fhir_request_eob_success_mock(self, url, request):
        # Return successful respose for EOB FHIR requests
        return mock_fhir_responses['success_eob']

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_COVERAGE_PATH)
    def fhir_request_coverage_success_mock(self, url, request):
        # Return successful respose for coverage FHIR requests
        return mock_fhir_responses['success_coverage']

    @override_switch('require-scopes', active=True)
    def _authorize_and_request_token(self, payload, application):
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://example.it',
            'client_id': application.client_id,
        }
        return self.client.post(reverse('oauth2_provider:token'), data=token_request_data)

    def _assertScopeResponse(self, scope, scopes_granted_access_token, response, content):
        # Assert expected response and content for scope vs. what is granted.
        if scope in scopes_granted_access_token:
            # Path is allowed by scopes.
            self.assertEqual(response.status_code, 200)
        else:
            # Path is NOT allowed by scopes.
            self.assertEqual(response.status_code, 403)

    def test_post_with_restricted_scopes_issues_token_with_same_scopes(self):
        """
        Test that when user unchecks some of the scopes the token is issued
        with the checked scopes only.
        """
        # create a user
        self._create_user('anna', '123456')
        # create a couple of capabilities
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability_a, capability_b)
        # user logs in
        self.client.login(username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://example.it',
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self._authorize_and_request_token(payload, application)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))
        # and here we test that only the capability-a scope has been issued
        self.assertEqual(content['scope'], "capability-a")

    @override_switch('require-scopes', active=True)
    def test_post_with_share_demographic_scopes(self):
        """
        Test authorization related to different, beneficiary "share_demographic_scopes",
        application.require_demographic_scopes, and requested scopes values.

        The "VIEW_OAUTH2_SCOPES_TEST_CASES" dictionary of test cases
            for the different values is used.
        """
        # create a user
        self._create_user('anna', '123456')

        # create an application and add some extra capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')

        # Give the app some additional scopes.
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        application.scope.add(capability_a, capability_b)

        # user logs in
        self.client.login(username='anna', password='123456')

        # Loop through test cases in dictionary
        cases = VIEW_OAUTH2_SCOPES_TEST_CASES
        for case in cases:
            # Setup request parameters for test case
            request_bene_share_demographic_scopes = cases[case]["request_bene_share_demographic_scopes"]
            request_app_requires_demographic = cases[case]["request_app_requires_demographic"]
            request_scopes = cases[case]["request_scopes"]

            # Setup expected results for test case
            result_has_error = cases[case]["result_has_error"]
            result_raises_exception = cases[case].get("result_raises_exception", None)
            result_exception_mesg = cases[case].get("result_exception_mesg", None)
            result_token_scopes_granted = cases[case].get("result_token_scopes_granted", None)
            result_access_token_count = cases[case].get("result_access_token_count", None)
            result_refresh_token_count = cases[case].get("result_refresh_token_count", None)
            result_archived_token_count = cases[case].get("result_archived_token_count", None)
            result_archived_data_access_grant_count = cases[case].get("result_archived_data_access_grant_count", None)

            payload = {
                'client_id': application.client_id,
                'response_type': 'code',
                'redirect_uri': 'http://example.it',
                'expires_in': 86400,
                'allow': True,
            }

            # Does the application choose to require demographic info?
            application.require_demographic_scopes = request_app_requires_demographic
            application.save()

            # Does the beneficiary choose to block demographic info?
            if request_bene_share_demographic_scopes is not None:
                payload['share_demographic_scopes'] = request_bene_share_demographic_scopes

            # Scopes to be requested in the authorization request
            if request_scopes is not None:
                payload['scope'] = ' '.join(request_scopes)

            # Perform authorization request
            if result_has_error:
                # Expecting an error with request
                with self.assertRaisesRegexp(result_raises_exception, result_exception_mesg):
                    response = self._authorize_and_request_token(payload, application)
                # Continue to next test case
                continue
            else:
                # Expecting no errors with request
                response = self._authorize_and_request_token(payload, application)

            # Assert auth request was successful
            self.assertEqual(response.status_code, 200)
            content = json.loads(response.content.decode("utf-8"))

            # Test scope in response content
            self.assertEqual(sorted(content['scope'].split()), sorted(result_token_scopes_granted))

            # Test scope in access_token
            at = AccessToken.objects.get(token=content['access_token'])
            scopes_granted_access_token = sorted(at.scope.split())
            self.assertEqual(scopes_granted_access_token, sorted(result_token_scopes_granted))

            # Verify token counts expected.
            if result_access_token_count:
                self.assertEqual(AccessToken.objects.count(), result_access_token_count)
            if result_refresh_token_count:
                self.assertEqual(RefreshToken.objects.count(), result_refresh_token_count)
            if result_archived_token_count:
                self.assertEqual(ArchivedToken.objects.count(), result_archived_token_count)
            if result_archived_data_access_grant_count:
                self.assertEqual(ArchivedDataAccessGrant.objects.count(), result_archived_data_access_grant_count)
            # Verify DataAccessGrant count is always = 1
            if result_archived_data_access_grant_count:
                self.assertEqual(DataAccessGrant.objects.count(), 1)

            # Test end points with APIClient
            # Test that resource end points are limited by scopes
            # Loop through all scope paths.
            for scope in SCOPES_TO_URL_BASE_PATH:
                base_path = SCOPES_TO_URL_BASE_PATH[scope]["base_path"]
                is_fhir_url = SCOPES_TO_URL_BASE_PATH[scope]["is_fhir_url"]
                test_readview = SCOPES_TO_URL_BASE_PATH[scope].get("test_readview", False)

                # Setup token in APIClient
                client = APIClient()
                client.credentials(HTTP_AUTHORIZATION="Bearer " + at.token)

                # Mock back end FHIR resource calls
                with HTTMock(self.fhir_request_patient_readview_success_mock,
                             self.fhir_request_patient_searchview_success_mock,
                             self.fhir_request_eob_success_mock,
                             self.fhir_request_coverage_success_mock):

                    # Is this a FHIR type URL?
                    if is_fhir_url:
                        # Test SearchView for base path
                        response = client.get(base_path)
                        content = json.loads(response.content)
                        self._assertScopeResponse(scope, scopes_granted_access_token, response, content)

                        # Test Searchiew for base path with ending "/"
                        response = client.get(base_path + "/")
                        content = json.loads(response.content)
                        self._assertScopeResponse(scope, scopes_granted_access_token, response, content)

                        # Test ReadView for base path with FHIR_ID
                        if test_readview:
                            response = client.get(base_path + "/" + settings.DEFAULT_SAMPLE_FHIR_ID)
                            content = json.loads(response.content)
                            self._assertScopeResponse(scope, scopes_granted_access_token, response, content)

                        # Test SearchView for base path with FHIR_ID
                        response = client.get(base_path + "?" + settings.DEFAULT_SAMPLE_FHIR_ID)
                        content = json.loads(response.content)
                        self._assertScopeResponse(scope, scopes_granted_access_token, response, content)
                    else:
                        # Test base path.
                        response = client.get(base_path)
                        content = json.loads(response.content)
                        self._assertScopeResponse(scope, scopes_granted_access_token, response, content)


class TestTokenView(BaseApiTest):
    test_uuid = "0123456789abcdefghijklmnopqrstuvwxyz"
    test_username = "0123456789abcdefghijklmnopqrstuvwxyz"

    def _create_test_token(self, user, application):
        # user logs in
        self.client.force_login(user)
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': application.redirect_uris,
            'scope': application.scopes().split(" "),
            'expires_in': 86400,
            'allow': True,
        }
        if application.authorization_grant_type == Application.GRANT_IMPLICIT:
            payload['response_type'] = 'token'
        response = self.client.post('/v1/o/authorize/', data=payload)
        self.client.logout()
        if response.status_code != 302:
            raise Exception(response.context_data)
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        if application.authorization_grant_type == Application.GRANT_IMPLICIT:
            fragment = parse_qs(urlparse(response['Location']).fragment)
            tkn = fragment.pop('access_token')[0]
        else:
            query_dict = parse_qs(urlparse(response['Location']).query)
            authorization_code = query_dict.pop('code')
            token_request_data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': application.redirect_uris,
                'client_id': application.client_id,
                'client_secret': application.client_secret,
            }

            response = self.client.post('/v1/o/token/', data=token_request_data)
            self.assertEqual(response.status_code, 200)
            # Now we have a token and refresh token
            tkn = response.json()['access_token']

        t = AccessToken.objects.get(token=tkn)
        return t

    def _create_authorization_header(self, client_id, client_secret):
        return "Basic {0}".format(base64.b64encode("{0}:{1}".format(client_id, client_secret).encode('utf-8')).decode('utf-8'))

    def _create_authentication_header(self, username):
        return "SLS {0}".format(base64.b64encode(username.encode('utf-8')).decode("utf-8"))

    def test_get_tokens_success(self):
        anna = self._create_user(self.test_username, '123456')
        # create a couple of capabilities
        capability_a = self._create_capability('token_management', [['GET', '/v1/o/tokens/']], default=False)
        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability_a)
        self._create_test_token(anna, application)
        response = self.client.get(reverse('token_management:token-list'),
                                   HTTP_AUTHORIZATION=self._create_authorization_header(application.client_id,
                                                                                        application.client_secret),
                                   HTTP_X_AUTHENTICATION=self._create_authentication_header(self.test_uuid))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        expected = [{
            # can't predict the id in this case
            'id': result[0]['id'],
            'user': anna.id,
            'application': {
                'id': application.id,
                'name': 'an app',
                'logo_uri': '',
                'tos_uri': '',
                'policy_uri': '',
                'contacts': ''
            },
        }]
        self.assertEqual(result, expected)

    def test_get_tokens_on_inactive_app(self):
        anna = self._create_user(self.test_username, '123456')
        # create a couple of capabilities
        capability_a = self._create_capability('token_management', [['GET', '/v1/o/tokens/']], default=False)
        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability_a)
        application.active = False
        application.save()
        # create token in self._create_test_token will check app.active for access control
        with self.assertRaises(Exception) as e:
            self._create_test_token(anna, application)

        msg_expected = settings.APPLICATION_TEMPORARILY_INACTIVE.format("an app")
        err_msg = str(e.exception)
        found = True
        index = -1
        try:
            index = err_msg.index(msg_expected)
        except ValueError:
            found = False
        self.assertTrue(index >= 0)
        self.assertTrue(found)

        application.active = True
        application.save()

    def test_delete_token_success(self):
        anna = self._create_user(self.test_username, '123456', fhir_id='19990000000002')
        bob = self._create_user('bob',
                                '123456',
                                fhir_id='19990000000001',
                                user_hicn_hash="86228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7",
                                user_mbi_hash="98765432137efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7")
        # create a couple of capabilities
        capability_a = self._create_capability('token_management', [['DELETE', r'/v1/o/tokens/\d+/']], default=False)
        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability_a)
        other_application = self._create_application(
            'another app', grant_type=Application.GRANT_IMPLICIT,
            client_type=Application.CLIENT_PUBLIC,
            redirect_uris='http://example.it',
            user=application.user,
        )
        other_application.scope.add(capability_a)
        tkn = self._create_test_token(anna, application)

        self.assertTrue(DataAccessGrant.objects.filter(
            beneficiary=anna,
            application=application,
        ).exists())

        # Post Django 2.2:  An OSError exception is expected when trying to reach the
        #                   backend FHIR server and proves authentication worked.
        with self.assertRaisesRegexp(OSError, "Could not find the TLS certificate file"):
            response = self.client.get('/v1/fhir/Patient',
                                       HTTP_AUTHORIZATION="Bearer " + tkn.token)

        bob_tkn = self._create_test_token(bob, other_application)
        self.assertTrue(DataAccessGrant.objects.filter(
            beneficiary=bob,
            application=other_application,
        ).exists())

        response = self.client.get(reverse('token_management:token-list'),
                                   HTTP_AUTHORIZATION=self._create_authorization_header(application.client_id,
                                                                                        application.client_secret),
                                   HTTP_X_AUTHENTICATION=self._create_authentication_header(self.test_uuid))
        grant_list = response.json()
        self.assertEqual(1, len(grant_list))
        response = self.client.delete(reverse('token_management:token-detail', args=[grant_list[0]['id']]),
                                      HTTP_AUTHORIZATION=self._create_authorization_header(application.client_id,
                                                                                           application.client_secret),
                                      HTTP_X_AUTHENTICATION=self._create_authentication_header(self.test_uuid))
        self.assertEqual(response.status_code, 204)
        failed_response = self.client.delete(reverse('token_management:token-detail', args=[grant_list[0]['id']]),
                                             HTTP_AUTHORIZATION=self._create_authorization_header(application.client_id,
                                                                                                  application.client_secret),
                                             HTTP_X_AUTHENTICATION=self._create_authentication_header(self.test_uuid))
        self.assertEqual(failed_response.status_code, 404)
        response = self.client.get('/v1/fhir/Patient',
                                   HTTP_AUTHORIZATION="Bearer " + tkn.token)
        self.assertEqual(response.status_code, 401)

        self.assertFalse(DataAccessGrant.objects.filter(
            beneficiary=anna,
            application=application,
        ).exists())

        # Post Django 2.2:  An OSError exception is expected when trying to reach the
        #                   backend FHIR server and proves authentication worked.
        with self.assertRaisesRegexp(OSError, "Could not find the TLS certificate file"):
            response = self.client.get('/v1/fhir/Patient',
                                       HTTP_AUTHORIZATION="Bearer " + bob_tkn.token)

        next_tkn = self._create_test_token(anna, application)

        # Post Django 2.2:  An OSError exception is expected when trying to reach the
        #                   backend FHIR server and proves authentication worked.
        with self.assertRaisesRegexp(OSError, "Could not find the TLS certificate file"):
            response = self.client.get('/v1/fhir/Patient',
                                       HTTP_AUTHORIZATION="Bearer " + next_tkn.token)

        # self.assertEqual(next_tkn.token, tkn.token)
        self.assertTrue(DataAccessGrant.objects.filter(
            beneficiary=anna,
            application=application,
        ).exists())

    def test_create_token_fail(self):
        self._create_user(self.test_username, '123456')

        # create a couple of capabilities
        capability_a = self._create_capability('token_management', [['POST', '/v1/o/tokens/']], default=False)
        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability_a)
        response = self.client.post(reverse('token_management:token-list'),
                                    HTTP_AUTHORIZATION=self._create_authorization_header(application.client_id,
                                                                                         application.client_secret),
                                    HTTP_X_AUTHENTICATION=self._create_authentication_header(self.test_uuid))
        self.assertEqual(response.status_code, 405)

    def test_update_token_fail(self):
        anna = self._create_user(self.test_username, '123456')
        # create a couple of capabilities
        capability_a = self._create_capability('token_management', [['PUT', r'/v1/o/tokens/\d+/']], default=False)
        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability_a)
        tkn = self._create_test_token(anna, application)
        response = self.client.put(reverse('token_management:token-detail', args=[tkn.pk]),
                                   HTTP_AUTHORIZATION=self._create_authorization_header(application.client_id,
                                                                                        application.client_secret),
                                   HTTP_X_AUTHENTICATION=self._create_authentication_header(self.test_uuid))
        self.assertEqual(response.status_code, 405)

    def test_unauthorized_fail(self):
        anna = self._create_user(self.test_username, '123456')
        # create a couple of capabilities
        self._create_capability('token_management', [['GET', '/v1/o/tokens/']], default=False)
        capability = self._create_capability('test', [], default=True)
        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability)
        self._create_test_token(anna, application)

        response = self.client.get(reverse('token_management:token-list'),
                                   HTTP_AUTHORIZATION=self._create_authorization_header(application.client_id,
                                                                                        application.client_secret),
                                   HTTP_X_AUTHENTICATION=self._create_authentication_header(self.test_uuid))
        self.assertEqual(response.status_code, 403)
