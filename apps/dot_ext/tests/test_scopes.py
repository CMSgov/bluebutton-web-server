from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf import settings
from oauth2_provider.scopes import get_scopes_backend

from apps.dot_ext.scopes import CapabilitiesScopes
from apps.test import BaseApiTest


class TestScopesBackendClass(BaseApiTest):
    def test_scopes_class_setting_is_set_to_capabilities_scopes(self):
        """
        Test that the SCOPES_BACKEND_CLASS has been set to
        dot_ext.scopes.CapabilitiesScopes.
        """
        assert settings.OAUTH2_PROVIDER['SCOPES_BACKEND_CLASS'] == 'apps.dot_ext.scopes.CapabilitiesScopes'
        assert isinstance(get_scopes_backend(), CapabilitiesScopes)

    def test_get_all_scopes(self):
        """
        Test that 'get_all_scopes' method return a dict-like object
        based on all the ProtectedCapability instance.
        """
        # create some capabilities
        self._create_capability('Capability A', [])
        self._create_capability('Capability B', [])
        self._create_capability('Capability C', [])
        # retrieve the list of all the scopes
        all_scopes = CapabilitiesScopes().get_all_scopes()
        assert all_scopes == {
            'capability-a': 'Capability A',
            'capability-b': 'Capability B',
            'capability-c': 'Capability C',
        }

    def test_get_available_scopes(self):
        """
        Test that 'get_available_scopes' method returns a list of scopes
        based on the ProtectedCapability related to the `application` parameter.
        """
        # create some capabilities
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        self._create_capability('Capability C', [])
        # create an application and bound scopes to it
        application = self._create_application('an app')
        application.scope.add(capability_a, capability_b)
        # retrieve the list of the scopes available for the application
        available_scopes = CapabilitiesScopes().get_available_scopes(application=application)
        assert available_scopes == ['capability-a', 'capability-b']

    def test_get_default_scopes(self):
        """
        Test that 'get_default_scopes' method returns a list of scopes
        based on the ProtectedCapability related to the `application` parameter.
        """
        # create some capabilities
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        self._create_capability('Capability C', [])
        # create an application and bound scopes to it
        application = self._create_application('an app')
        application.scope.add(capability_a, capability_b)
        # retrieve the list of the scopes available for the application
        default_scopes = CapabilitiesScopes().get_default_scopes(application=application)
        assert default_scopes == ['capability-a', 'capability-b']

    def test_backend_works_with_no_capabilities(self):
        """
        Test the backend works when there are no capabilities in the system.
        """
        # create an application and bound scopes to it
        application = self._create_application('an app')
        # retrieve the list of all the scopes
        all_scopes = CapabilitiesScopes().get_all_scopes()
        assert all_scopes == {}
        # retrieve the list of the scopes available for the application
        available_scopes = CapabilitiesScopes().get_available_scopes(application=application)
        assert available_scopes == []
        # retrieve the list of the scopes available for the application
        default_scopes = CapabilitiesScopes().get_default_scopes(application=application)
        assert default_scopes == []
