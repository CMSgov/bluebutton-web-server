from __future__ import absolute_import
from __future__ import unicode_literals

from ...test import BaseApiTest


class TestApplicationModel(BaseApiTest):
    def test_allow_resource_method_return_false_for_forbidden_resource(self):
        # create an empty capability
        capability = self._create_capability('Capability', [])
        # create an application with the capability
        app = self._create_application('john_app', capability=capability)
        self.assertFalse(app.allow_resource('GET', '/api/foo/'))

    def test_allow_resource_method_return_true_for_allowed_resource(self):
        # create a capability
        capability = self._create_capability('Capability', [['GET', '/api/foo/']])
        # create an application with the capability
        app = self._create_application('john_app', capability=capability)
        self.assertTrue(app.allow_resource('GET', '/api/foo/'))

    def test_allow_resource_with_patterns(self):
        # create a capability that uses urls with '[*]' patterns
        capability = self._create_capability(
            'Capability', [
                ['GET', '/api/foo/[id]/'],
                ['GET', '/api/foo/[id]/bar/[id]'],
            ]
        )
        # create an application with the capability
        app = self._create_application('john_app', capability=capability)
        self.assertFalse(app.allow_resource('GET', '/api/foo/'))
        self.assertTrue(app.allow_resource('GET', '/api/foo/1/'))
        self.assertTrue(app.allow_resource('GET', '/api/foo/1/bar/2'))
