import json
import base64
from django.conf import settings
from django.urls import reverse
from oauth2_provider.compat import parse_qs, urlparse
from oauth2_provider.models import AccessToken

from apps.test import BaseApiTest
from ..models import Application
from apps.authorization.models import DataAccessGrant
from apps.dot_ext.scopes import CapabilitiesScopes
from apps.capabilities.models import ProtectedCapability


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

    def test_post_with_block_personal_choice(self):
        """
        Test that when user chooses the block_personal_choice on
        the BENE consent form, that the correct scopes are blocked
        with the require-scopes feature switch DISABLED.
        """
        full_scopes_list = CapabilitiesScopes().get_default_scopes()
        non_personal_scopes_list = list(set(full_scopes_list) - set(settings.BENE_PERSONAL_INFO_SCOPES))

        # create a user
        self._create_user('anna', '123456')

        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        for s in full_scopes_list:
            capability = ProtectedCapability.objects.get(slug=s)
            application.scope.add(capability)

        # user logs in
        self.client.login(username='anna', password='123456')

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://example.it',
            'scope': ' '.join(full_scopes_list),
            'expires_in': 86400,
            'allow': True,
        }

        # 1. Test the authorization with block_personal_choice = None.
        response = self._authorize_and_request_token(payload, application)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))
        # and here we test that the full scopes have been issued
        self.assertEqual(sorted(content['scope'].split()), sorted(full_scopes_list))

        # 2. Test the authorization with block_personal_choice = False.
        payload['block_personal_choice'] = 'False'
        response = self._authorize_and_request_token(payload, application)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))
        # and here we test that the full scopes have been issued
        self.assertEqual(sorted(content['scope'].split()), sorted(full_scopes_list))

        # 3. Test the authorization with block_personal_choice = True.
        payload['block_personal_choice'] = 'True'
        response = self._authorize_and_request_token(payload, application)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))
        # and here we test that non-personal scopes have been issued
        self.assertEqual(sorted(content['scope'].split()), sorted(non_personal_scopes_list))


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

    def test_delete_token_success(self):
        anna = self._create_user(self.test_username, '123456', fhir_id='19990000000002')
        bob = self._create_user('bob',
                                '123456',
                                fhir_id='19990000000001',
                                user_id_hash="86228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7")
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
