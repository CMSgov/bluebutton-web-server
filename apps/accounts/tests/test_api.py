from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from apps.test import BaseApiTest


ENCODED = settings.ENCODING


class TestUserSelfEndpoint(BaseApiTest):
    """
    Tests for the /user/self/ api endpoint.
    """

    def test_user_self_post_method_forbidden(self):
        """
        Tests that POST requests to /user/self/ endpoint are forbidden.
        """
        response = self.client.post(reverse('openid_connect_userinfo'))
        self.assertEqual(response.status_code, 405)

    def test_user_self_get_fails_without_credentials(self):
        """
        Tests that GET requests to /connect/userinfo endpoint fail without
        a valid access_token.
        """
        response = self.client.get(reverse('openid_connect_userinfo'))
        self.assertEqual(response.status_code, 403)

    def test_user_self_get(self):
        """
        Tests that GET request to /connect/userinfo returns user details for
        the authenticated user.
        """
        # Create the user
        user = self._create_user('john',
                                 '123456',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')

        # Get an access token for the user 'john'
        access_token = self._get_access_token('john', '123456')
        # Authenticate the request with the bearer access token
        auth_headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % access_token}
        response = self.client.get(
            reverse('openid_connect_userinfo'), **auth_headers)
        self.assertEqual(response.status_code, 200)
        # Check if the content of the response corresponds to the expected json
        expected_json = {
            'sub': user.username,
            'name': "%s %s" % (user.first_name, user.last_name),
            'given_name': user.first_name,
            'family_name': user.last_name,
            'email': user.email,
            'iat': DjangoJSONEncoder().default(user.date_joined),
        }
        self.assertJSONEqual(response.content.decode(ENCODED), expected_json)


class TestSingleAccessTokenValidator(BaseApiTest):

    def test_single_access_token_issued(self):
        # create the user
        self._create_user('john',
                          '123456',
                          first_name='John',
                          last_name='Smith',
                          email='john@smith.net')
        # create a oauth2 application
        application = self._create_application('test')
        # get the first access token for the user 'john'
        first_access_token = self._get_access_token('john',
                                                    '123456',
                                                    application)
        # request another access token for the same user/application
        second_access_token = self._get_access_token('john',
                                                     '123456',
                                                     application)
        self.assertEqual(first_access_token, second_access_token)

    def test_single_access_token_issued_when_changed_scope_allowed(self):
        """
        Test that the same access token is issued when a scope is changed but
        it is a subset of the old token's scope.

        e.g. old_token_scope = 'read write'
             new_token_scope = 'read'
        """
        # create the user
        self._create_user('john',
                          '123456',
                          first_name='John',
                          last_name='Smith',
                          email='john@smith.net')
        # create read and write capabilities
        read_capability = self._create_capability('Read', [])
        write_capability = self._create_capability('Write', [])
        # create a oauth2 application and add capabilities
        application = self._create_application('test')
        application.scope.add(read_capability, write_capability)
        # get the first access token for the user 'john'
        first_access_token = self._get_access_token('john',
                                                    '123456',
                                                    application,
                                                    scope='read write')
        # request another access token for the same user/application
        second_access_token = self._get_access_token('john',
                                                     '123456',
                                                     application,
                                                     scope='read')
        self.assertEqual(first_access_token, second_access_token)

    def test_new_access_token_issued_when_scope_added(self):
        """
        Test that a new access token is issued when a scope is added.

        e.g. old_token_scope = 'read'
             new_token_scope = 'read write'
        """
        # create the user
        self._create_user('john',
                          '123456',
                          first_name='John',
                          last_name='Smith',
                          email='john@smith.net')
        # create read and write capabilities
        read_capability = self._create_capability('Read', [])
        write_capability = self._create_capability('Write', [])
        # create a oauth2 application and add capabilities
        application = self._create_application('test')
        application.scope.add(read_capability, write_capability)
        # get the first access token for the user 'john'
        first_access_token = self._get_access_token('john',
                                                    '123456',
                                                    application,
                                                    scope='read')
        # request another access token for the same user/application
        second_access_token = self._get_access_token('john',
                                                     '123456',
                                                     application,
                                                     scope='read write')
        self.assertNotEqual(first_access_token, second_access_token)
