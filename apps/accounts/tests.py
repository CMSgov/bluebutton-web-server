from __future__ import unicode_literals
from __future__ import absolute_import

from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse

from apps.utils.test import BaseApiTest


class TestUserSelfEndpoint(BaseApiTest):
    """
    Tests for the /user/self/ api endpoint.
    """

    def test_user_self_post_method_forbidden(self):
        """
        Tests that POST requests to /user/self/ endpoint are forbidden.
        """
        response = self.client.post(reverse('user_self'))
        self.assertEqual(response.status_code, 405)

    def test_user_self_get_fails_without_credentials(self):
        """
        Tests that GET requests to /user/self/ endpoint fail without
        a valid access_token.
        """
        response = self.client.get(reverse('user_self'))
        self.assertEqual(response.status_code, 403)

    def test_user_self_get(self):
        """
        Tests that GET request to /user/self/ returns user details for
        the authenticated user.
        """
        # Create the user
        user = self._create_user('john', '123456', first_name='John', last_name='Smith', email='john@smith.net')
        # Get an access token for the user 'john'
        access_token = self._get_access_token('john', '123456')
        # Authenticate the request with the bearer access token
        auth_headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % access_token}
        response = self.client.get(reverse('user_self'), **auth_headers)
        self.assertEqual(response.status_code, 200)
        # Check if the content of the response corresponds to the expected json
        expected_json = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'created': DjangoJSONEncoder().default(user.date_joined),
        }
        self.assertJSONEqual(response.content, expected_json)
