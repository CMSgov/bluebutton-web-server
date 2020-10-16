from django.utils import timezone
from datetime import timedelta
from oauth2_provider.compat import parse_qs, urlparse
from oauth2_provider.models import (
    get_application_model,
    get_access_token_model,
)
from django.urls import reverse
from apps.test import BaseApiTest
from apps.authorization.models import (
    DataAccessGrant,
    check_grants,
    update_grants,
)

Application = get_application_model()
AccessToken = get_access_token_model()


class TestDataAccessGrant(BaseApiTest):
    def test_creation_on_approval(self):
        redirect_uri = 'http://localhost'
        # create a user
        user = self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        # user logs in
        self.client.login(username='anna', password='123456')

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
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
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 200)

        # errors if DNE or more than one is found
        DataAccessGrant.objects.get(beneficiary=user.id, application=application.id)

    def test_no_action_on_reapproval(self):
        redirect_uri = 'http://localhost'
        # create a user
        user = self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        # user logs in
        self.client.login(username='anna', password='123456')

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
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
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 200)

        # errors if DNE or more than one is found
        DataAccessGrant.objects.get(beneficiary=user.id, application=application.id)

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
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
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 200)

        # errors if DNE or more than one is found
        DataAccessGrant.objects.get(beneficiary=user.id, application=application.id)

    def test_check_and_update_grants(self):
        redirect_uri = 'http://localhost'
        # create a user
        user = self._create_user('anna', '123456')
        user2 = self._create_user('bob', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        AccessToken.objects.create(
            token="existingtoken",
            user=user,
            application=application,
            expires=timezone.now() + timedelta(seconds=10),
        )

        checks = check_grants()
        self.assertGreater(
            checks['unique_tokens'],
            checks['grants'],
        )

        update_grants()

        checks = check_grants()
        self.assertEqual(
            checks['unique_tokens'],
            checks['grants'],
        )

        # create expired token
        AccessToken.objects.create(
            token="expiredtoken",
            user=user2,
            application=application,
            expires=timezone.now() - timedelta(seconds=10),
        )

        checks = check_grants()
        self.assertEqual(
            checks['unique_tokens'],
            checks['grants'],
        )

        update_grants()

        checks = check_grants()
        self.assertEqual(
            checks['unique_tokens'],
            checks['grants'],
        )

    def test_permission_deny_on_app_or_org_disabled(self):
        '''
        BB2-149 leverage application.active, user.is_active to deny permission
        to an application or applications under a user (organization)
        '''
        redirect_uri = 'http://localhost'
        # create a user
        user = self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            user=user,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a)
        application.active = False
        application.save()
        # user logs in
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
        self.assertEqual(response.status_code, 403)
        # pretty good evidence for in active app permission denied
        self.assertEqual(response.template_name, "app_inactive_403.html")
        # set back app and user to active - not to affect other tests
        application.active = True
        application.save()
