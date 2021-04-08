from datetime import timedelta
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from oauth2_provider.compat import parse_qs, urlparse
from oauth2_provider.models import (
    get_application_model,
    get_access_token_model,
)

from apps.authorization.models import (
    DataAccessGrant,
    check_grants,
    get_application_bene_grant_counts,
    update_grants,
)
from apps.fhir.bluebutton.models import check_crosswalks
from apps.test import BaseApiTest


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

    def test_get_application_bene_grant_counts(self):
        '''
        Test the get_application_bene_grant_counts() function
        from apps.authorization.models
        '''
        redirect_uri = 'http://localhost'

        # create capabilities
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])

        # create an application1 and add capabilities
        application1 = self._create_application(
            'application1',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application1.scope.add(capability_a, capability_b)

        # create dev2 user
        dev2_user = User.objects.create_user('dev2', password='123456')

        # create an application2 and add capabilities
        application2 = self._create_application(
            'application2',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            user=dev2_user,
            redirect_uris=redirect_uri)
        application2.scope.add(capability_a, capability_b)

        # Create 5x Real (positive FHIR_ID) users and access tokens for applicaiton1
        for cnt in range(5):
            user = self._create_user('johnsmith' + str(cnt), 'password',
                                     first_name='John1' + str(cnt),
                                     last_name='Smith',
                                     email='john' + str(cnt) + '@smith.net',
                                     fhir_id='2000000000000' + str(cnt),
                                     user_hicn_hash='239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt),
                                     user_mbi_hash='9876543217ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt))
            # create AC
            AccessToken.objects.create(
                token="existingtokenReal" + str(cnt),
                user=user,
                application=application1,
                expires=timezone.now() + timedelta(seconds=10),
            )

        # Create 7x Synthetic (negative FHIR_ID) users and access tokens for application2
        for cnt in range(7):
            user = self._create_user('johndoe' + str(cnt), 'password',
                                     first_name='John' + str(cnt),
                                     last_name='Doe',
                                     email='john' + str(cnt) + '@doe.net',
                                     fhir_id='-2000000000000' + str(cnt),
                                     user_hicn_hash='255e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt),
                                     user_mbi_hash='987654321aaaa11111aaaa195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt))
            # create AC
            AccessToken.objects.create(
                token="existingtoken1Synth" + str(cnt),
                user=user,
                application=application1,
                expires=timezone.now() + timedelta(seconds=10),
            )

        # Create 3x Real (positive FHIR_ID) users and access tokens for applicaiton2
        for cnt in range(3):
            user = self._create_user('joesmith' + str(cnt), 'password',
                                     first_name='Joe' + str(cnt),
                                     last_name='Smith',
                                     email='joe' + str(cnt) + '@smith.net',
                                     fhir_id='1000000000000' + str(cnt),
                                     user_hicn_hash='509e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt),
                                     user_mbi_hash='9076543217ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt))
            # create AC
            AccessToken.objects.create(
                token="existingtoken2Real" + str(cnt),
                user=user,
                application=application2,
                expires=timezone.now() + timedelta(seconds=10),
            )

        # Create 9x Synthetic (negative FHIR_ID) users and access tokens for application2
        for cnt in range(9):
            user = self._create_user('joedoe' + str(cnt), 'password',
                                     first_name='Joe' + str(cnt),
                                     last_name='Doe',
                                     email='joe' + str(cnt) + '@doe.net',
                                     fhir_id='-1000000000000' + str(cnt),
                                     user_hicn_hash='505e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt),
                                     user_mbi_hash='907654321aaaa11111aaaa195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt))
            # create AC
            AccessToken.objects.create(
                token="existingtoken2Synth" + str(cnt),
                user=user,
                application=application2,
                expires=timezone.now() + timedelta(seconds=10),
            )

        # Assert crosswalks counts
        self.assertEqual("{'synthetic': 16, 'real': 8}", str(check_crosswalks()))

        # This creates grants from access tokens. Does not test creation on approval (this is tested elsewhere).
        with transaction.atomic():
            update_grants()

        # Assert check_grants (all grants)
        self.assertEqual("{'unique_tokens': 24, 'grants': 24}", str(check_grants()))

        # Assert application1 get_application_bene_grant_counts()
        self.assertEqual("{'real': 5, 'synthetic': 7}", str(get_application_bene_grant_counts(application1.id)))

        # Assert application2 get_application_bene_grant_counts()
        self.assertEqual("{'real': 3, 'synthetic': 9}", str(get_application_bene_grant_counts(application2.id)))
