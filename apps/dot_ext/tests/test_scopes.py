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
        assert available_scopes == ['capability-a', 'capability-b', 'capability-c']

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
        assert default_scopes == ['capability-a', 'capability-b', 'capability-c']

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

    def test_condense_scopes(self):
        """
        Test that v2 scopes get properly condensed
        """
        scopes = [
            'patient/Patient.r',
            'patient/Patient.s',
            'patient/Patient.rs',
            'patient/Coverage.s',
            'patient/Coverage.rs',
            'patient/ExplanationOfBenefit.r',
            'patient/ExplanationOfBenefit.s'
        ]
        condensed_scopes = CapabilitiesScopes().condense_scopes(scopes)
        assert len(condensed_scopes) == 3
        assert 'patient/Patient.rs' in condensed_scopes
        assert 'patient/Coverage.rs' in condensed_scopes
        assert 'patient/ExplanationOfBenefit.rs' in condensed_scopes
        scopes = [
            'patient/Patient.r',
            'patient/Coverage.s',
            'patient/Coverage.rs',
            'patient/ExplanationOfBenefit.s',
            'profile'
        ]
        condensed_scopes = CapabilitiesScopes().condense_scopes(scopes)
        assert len(condensed_scopes) == 4
        assert 'patient/Patient.r' in condensed_scopes
        assert 'patient/Coverage.rs' in condensed_scopes
        assert 'patient/ExplanationOfBenefit.s' in condensed_scopes
        assert 'profile' in condensed_scopes
