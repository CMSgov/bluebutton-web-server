from __future__ import absolute_import
from __future__ import unicode_literals

from oauth2_provider.models import AccessToken

from apps.test import BaseApiTest

from ..permissions import allow_resource


class TestPermissions(BaseApiTest):
    def test_allow_resource_method_return_false_for_forbidden_resource(self):
        self._create_user('anna', '123456')
        # create an empty capability
        capability = self._create_capability('Capability', [])
        # create an application with the capability
        app = self._create_application('john_app', capability=capability)
        # retrieve a token to use with allowe_resource function
        token = self._get_access_token('anna', '123456', app)
        access_token = AccessToken.objects.get(token=token)
        self.assertFalse(allow_resource(access_token, 'GET', '/api/foo/'))

    def test_allow_resource_method_return_true_for_allowed_resource(self):
        self._create_user('anna', '123456')
        # create a capability
        capability = self._create_capability('Capability', [['GET', '/api/foo/']])
        # create an application with the capability
        app = self._create_application('john_app', capability=capability)
        # retrieve a token to use with allowe_resource function
        token = self._get_access_token('anna', '123456', app)
        access_token = AccessToken.objects.get(token=token)
        self.assertTrue(allow_resource(access_token, 'GET', '/api/foo/'))

    def test_allow_resource_with_patterns(self):
        self._create_user('anna', '123456')
        # create a capability that uses urls with '[*]' patterns
        capability = self._create_capability(
            'Capability', [
                ['GET', '/api/foo/[id]/'],
                ['GET', '/api/foo/[id]/bar/[id]'],
            ]
        )
        # create an application with the capability
        app = self._create_application('john_app', capability=capability)
        # retrieve a token to use with allowe_resource function
        token = self._get_access_token('anna', '123456', app)
        access_token = AccessToken.objects.get(token=token)
        self.assertFalse(allow_resource(access_token, 'GET', '/api/foo/'))
        self.assertTrue(allow_resource(access_token, 'GET', '/api/foo/1/'))
        self.assertTrue(allow_resource(access_token, 'GET', '/api/foo/1/bar/2'))
