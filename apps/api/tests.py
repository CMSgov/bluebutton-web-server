from __future__ import absolute_import
from __future__ import unicode_literals

import json

from django.conf import settings
from django.core.urlresolvers import reverse

from ..test import BaseApiTest


ENCODED = settings.ENCODING


class TestApi(BaseApiTest):
    """
    Tests for the api endpoints.
    """

    def test_api_read_get_fails_without_credentials(self):
        """
        Tests that GET requests to api_read endpoint fail without
        a valid access_token.
        """
        response = self.client.get(reverse('api_read'))
        self.assertEqual(response.status_code, 403)

    def test_api_read_get_fails_without_capabilities(self):
        """
        Test that GET requests to api_read enpoint fail when
        the application used to obtain tokens does not have
        a proper cabapility associated.
        """
        # Create the user to obtain the token
        self._create_user('john', '123456')
        capability = self._create_capability('test', [['GET', '/api/foo']])
        application = self._create_application('test', capability=capability)
        access_token = self._get_access_token('john', '123456', application=application)
        # Authenticate the request with the bearer access token
        auth_headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % access_token}
        response = self.client.get(reverse('api_read'), **auth_headers)
        self.assertEqual(response.status_code, 403)

    def test_api_read_get(self):
        """
        Tests that api_read returns proper response.
        """
        # Create the user to obtain the token
        self._create_user('john', '123456')
        # Create an application with capability to read /api/read endpoint
        capability = self._create_capability('test', [['GET', '/api/read']])
        application = self._create_application('test', capability=capability)
        access_token = self._get_access_token('john', '123456', application=application)
        # Authenticate the request with the bearer access token
        auth_headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % access_token}
        response = self.client.get(reverse('api_read'), **auth_headers)
        self.assertEqual(response.status_code, 200)

        self.assertJSONEqual(response.content.decode(ENCODED),
                             {'hello': 'World', 'oauth2': True})

    def test_api_write_get_fails_without_credentials(self):
        """
        Tests that GET requests to api_write endpoint fail without
        a valid access_token.
        """
        response = self.client.get(reverse('api_write'))
        self.assertEqual(response.status_code, 403)

    def test_api_write_post_fails_without_credentials(self):
        """
        Tests that POST requests to api_write endpoint fail without
        a valid access_token.
        """
        response = self.client.post(reverse('api_write'), data={'test': 'data'})
        self.assertEqual(response.status_code, 403)

    def test_api_write_post_fails_without_capabilities(self):
        """
        Test that POST requests to api_write enpoint fail when
        the application used to obtain tokens does not have
        a proper cabapility associated.
        """
        # Create the user to obtain the token
        self._create_user('john', '123456')
        capability = self._create_capability('test', [['GET', '/api/foo']])
        application = self._create_application('test', capability=capability)
        access_token = self._get_access_token('john', '123456', application=application)
        # Authenticate the request with the bearer access token
        auth_headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % access_token}
        response = self.client.get(reverse('api_read'), **auth_headers)
        self.assertEqual(response.status_code, 403)

    def test_api_write_post(self):
        """
        Tests that api_write returns proper response.
        """
        # Create the user to obtain the token
        self._create_user('john', '123456')
        capability = self._create_capability('test', [['POST', '/api/write']])
        application = self._create_application('test', capability=capability)
        access_token = self._get_access_token('john', '123456', application=application)
        # Prepare data for post request
        data = json.dumps({'test': 'data'})
        # Authenticate the request with the bearer access token
        auth_headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % access_token}
        response = self.client.post(reverse('api_write'),
                                    data=data,
                                    content_type='application/json',
                                    **auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(ENCODED),
                             {'test': 'data', 'write': True})
