import json
import base64
from time import strftime

import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
# from oauth2_provider.compat import parse_qs, urlparse
from urllib.parse import parse_qs, urlparse
from oauth2_provider.models import get_access_token_model, get_refresh_token_model
from django.http import HttpRequest
from django.urls import reverse
from django.test import Client

from apps.test import BaseApiTest
from ..models import Application, ArchivedToken
from apps.authorization.models import DataAccessGrant, ArchivedDataAccessGrant

AccessToken = get_access_token_model()
RefreshToken = get_refresh_token_model()


class TestAuthorizeWithCustomScheme(BaseApiTest):

    def _create_authorization_header(self, client_id, client_secret):
        return "Basic {0}".format(
            base64.b64encode("{0}:{1}".format(client_id, client_secret).encode('utf-8')).decode('utf-8'))

    def test_post_with_valid_non_standard_scheme_granttype_authcode_clienttype_public(self):
        # Test with application setup as grant_type=authorization_code and client_type=public
        redirect_uri = 'com.custom.bluebutton://example.it'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_PUBLIC,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')

        code_challenge = "sZrievZsrYqxdnu2NVD603EiYBM18CuzZpwB-pOSZjo"

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        response = self.client.get('/v1/o/authorize', data=payload)
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        response = self.client.post(response['Location'], data=payload)

        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
        }
        # Test that using a BAD code_verifier has a bad request response
        token_request_data.update({'code_verifier': 'test1234567bad9verifier23456789123456789123456789'})
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 400)

        # Test that using a GOOD code_verifier is successful
        token_request_data.update({'code_verifier': 'test123456789123456789123456789123456789123456789'})
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 200)

        # Test 2nd access token request is unauthorized
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 400)

    def test_post_with_invalid_non_standard_scheme_granttype_authcode_clienttype_public(self):
        redirect_uri = 'com.custom.bluebutton://example.it'
        bad_redirect_uri = 'com.custom.bad://example.it'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_PUBLIC,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': bad_redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.assertEqual(response.status_code, 400)

    def test_post_with_valid_non_standard_scheme_granttype_authcode_clienttype_confidential(self):
        # Test with application setup as grant_type=authorization_code and client_type=confidential
        redirect_uri = 'com.custom.bluebutton://example.it'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')

        code_challenge = "sZrievZsrYqxdnu2NVD603EiYBM18CuzZpwB-pOSZjo"

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        response = self.client.get('/v1/o/authorize', data=payload)
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        response = self.client.post(response['Location'], data=payload)

        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
        }
        # Test that request is unauthorized WITH OUT the client_secret.
        token_request_data.update({'code_verifier': 'test123456789123456789123456789123456789123456789'})
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 401)

        # Setup application's client_secret
        token_request_data.update({'client_secret': application.client_secret_plain})

        # Test that using a BAD code_verifier has a bad request response
        token_request_data.update({'code_verifier': 'test1234567bad9verifier23456789123456789123456789'})
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 400)

        # Test that request is successful WITH the client_secret and GOOD code_verifier
        token_request_data.update({'code_verifier': 'test123456789123456789123456789123456789123456789'})
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 200)

        # Test 2nd access token request is unauthorized
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 400)

    def test_post_with_invalid_non_standard_scheme_granttype_authcode_clienttype_confidential(self):
        # Test with application setup as grant_type=authorization_code and client_type=confidential
        redirect_uri = 'com.custom.bluebutton://example.it'
        bad_redirect_uri = 'com.custom.bad://example.it'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': bad_redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.assertEqual(response.status_code, 400)

    def test_refresh_token(self):
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        refresh_tkn = response.json()['refresh_token']
        refresh_request_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_tkn,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=refresh_request_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['access_token'], tkn)

    def test_refresh_with_expired_token(self):
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        refresh_tkn = response.json()['refresh_token']
        at = AccessToken.objects.get(token=tkn)
        at.delete()
        refresh_request_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_tkn,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=refresh_request_data)
        self.assertEqual(response.status_code, 400)

    def test_refresh_13_month_with_expired_grant(self):
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        refresh_tkn = response.json()['refresh_token']
        at = AccessToken.objects.get(token=tkn)
        dag = DataAccessGrant.objects.get(
            beneficiary=at.user,
            application=application
        )
        dag.expiration_date = datetime.now().replace(
            tzinfo=pytz.UTC
        ) + relativedelta(months=-1)
        dag.save()
        at.delete()
        refresh_request_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_tkn,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=refresh_request_data)
        self.assertEqual(response.status_code, 400)

    def test_refresh_with_one_time_access_retrieve_app_using_refresh_token(self):
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        refresh_tkn = response.json()['refresh_token']
        at = AccessToken.objects.get(token=tkn)
        at.delete()
        # request refresh token without passing client_id
        refresh_request_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_tkn,
            'redirect_uri': redirect_uri,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=refresh_request_data)
        self.assertEqual(response.status_code, 401)

    def test_refresh_with_one_time_access_retrieve_app_from_auth_header(self):
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        refresh_tkn = response.json()['refresh_token']
        at = AccessToken.objects.get(token=tkn)
        at.delete()
        # request refresh token without passing client_id
        refresh_request_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_tkn,
            'redirect_uri': redirect_uri,
        }
        auth = self._create_authorization_header(application.client_id, application.client_secret_plain)
        response = self.client.post(
            reverse('oauth2_provider:token'),
            data=refresh_request_data,
            HTTP_AUTHORIZATION=auth,
        )
        self.assertEqual(response.status_code, 400)

    def test_dag_expiration_exists(self):
        redirect_uri = 'http://localhost'

        # create a user
        user = self._create_user('anna', '123456')

        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri,
            data_access_type="THIRTEEN_MONTH",
        )
        capability_a = self._create_capability('Capability A', [])
        application.scope.add(capability_a)

        # create a data access grant
        expiration_date = datetime.now() + relativedelta(months=+13)
        dag = DataAccessGrant(beneficiary=user, application=application, expiration_date=expiration_date)
        dag.save()

        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')

        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()

        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        tkn = response.json()
        expiration_date_string = strftime('%Y-%m-%dT%H:%M:%SZ', expiration_date.timetuple())
        self.assertEqual(tkn["access_grant_expiration"][:-4], expiration_date_string[:-4])

    def test_revoke_endpoint(self):
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # extract token and use it to make a revoke request
        tkn = response.json()['access_token']
        revoke_request_data = f"token={tkn}&client_id={application.client_id}&client_secret={application.client_secret_plain}"
        content_type = "application/x-www-form-urlencoded"
        c = Client()
        rev_response = c.post('/v1/o/revoke/', data=revoke_request_data, content_type=content_type)
        self.assertEqual(rev_response.status_code, 200)
        # check DAG deletion
        dags_count = DataAccessGrant.objects.count()
        self.assertEqual(dags_count, 0)
        # check token deletion
        tkn_count = AccessToken.objects.filter(token=tkn).count()
        self.assertEqual(tkn_count, 0)

    def test_refresh_with_revoked_token(self):
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        revoke_request_data = {
            'token': tkn,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        rev_response = c.post('/v1/o/revoke_token/', data=revoke_request_data)
        self.assertEqual(rev_response.status_code, 200)
        archived_token = ArchivedToken.objects.get(token=tkn)
        self.assertEqual(application.id, archived_token.application.id)
        self.assertEqual(tkn, archived_token.token)
        refresh_tkn = response.json()['refresh_token']
        refresh_request_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_tkn,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=refresh_request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'{"error": "invalid_grant"}')

    def test_application_delete_after_auth(self):
        # Test that there are no errors with cascading deletes
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        refresh_tkn = response.json()['refresh_token']

        # Test for cascading contraint errors.
        application_pk = application.pk
        application.delete()
        # Test related objects are deleted
        self.assertFalse(AccessToken.objects.filter(token=tkn).exists())
        self.assertTrue(ArchivedToken.objects.filter(token=tkn).exists())
        self.assertFalse(RefreshToken.objects.filter(token=refresh_tkn).exists())
        self.assertFalse(DataAccessGrant.objects.filter(application__pk=application_pk).exists())
        self.assertTrue(ArchivedDataAccessGrant.objects.filter(application__pk=application_pk).exists())

    def test_user_delete_after_auth(self):
        # Test that there are no errors with cascading deletes
        redirect_uri = 'http://localhost'
        # create a user
        user = self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        refresh_tkn = response.json()['refresh_token']

        # Test for cascading contraint errors.
        user_pk = user.pk
        user.delete()
        # Test related objects are deleted
        self.assertFalse(AccessToken.objects.filter(token=tkn).exists())
        self.assertTrue(ArchivedToken.objects.filter(token=tkn).exists())
        self.assertFalse(RefreshToken.objects.filter(token=refresh_tkn).exists())
        self.assertFalse(DataAccessGrant.objects.filter(beneficiary__pk=user_pk).exists())
        self.assertTrue(ArchivedDataAccessGrant.objects.filter(beneficiary__pk=user_pk).exists())

    def test_revoked_token_on_inactive_app(self):
        '''
        BB2-149:
        adapted from existing token revoke test
        to test revoke on an inactive app
        '''
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        revoke_request_data = {
            'token': tkn,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        # set app to inactive before revoke
        application.active = False
        application.save()

        msg_expected = "invalid_client"
        response = c.post('/v1/o/revoke_token/', data=revoke_request_data)
        # assert 403 and content json is expected message
        self.assertEqual(response.status_code, 401)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content['error'], msg_expected)

        # revert app to active in case not to impact other tests
        application.active = True
        application.save()

    def test_introspect_token_on_inactive_app(self):
        '''
        BB2-149:
        adapted from token auth test but test token introspect on a inactive app,
        403 customized permission denied message expected.
        '''
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        capability_introspect = self._create_capability('introspection', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b, capability_introspect)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a', 'capability-b', 'introspection'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }
        c = Client()
        response = c.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        introspect_request_data = {
            'token': tkn,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
        }

        auth_headers = {'Authorization': 'Bearer %s' % tkn}

        # set app to inactive before introspect
        application.active = False
        application.save()

        msg_expected = "invalid_client"
        response = c.post('/v1/o/introspect/', data=introspect_request_data, **auth_headers)
        # asssert 401 and content json message
        self.assertEqual(response.status_code, 401)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content['error'], msg_expected)

        # revert app to active in case not to impact other tests
        application.active = True
        application.save()
