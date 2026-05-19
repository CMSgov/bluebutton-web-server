import json
from types import SimpleNamespace

from django.test import TestCase

from apps.utils import has_matching_protected_resource


class IsValidScopeTest(TestCase):
    def setUp(self):
        eob_protected_resources = json.dumps(['GET', '/v[123]/fhir/ExplanationOfBenefit[/?].*$'])
        coverage_protected_resources = json.dumps(['GET', '/v[123]/fhir/Coverage[/]?$'])
        self.protected_resources = [eob_protected_resources, coverage_protected_resources]

    def test_is_valid_scope_returns_false(self) -> bool:
        """
        Returns False since the app has EOB and Coverage scopes but is trying to make a Patient call.
        """
        request = SimpleNamespace(path='/v3/fhir/Patient', method='GET')
        has_match = has_matching_protected_resource(self.protected_resources, request)

        assert has_match is False

    def test_is_valid_scope_returns_true(self) -> bool:
        """
        Returns True since the app has EOB and Coverage scopes and is trying to make a Coverage call.
        """
        request = SimpleNamespace(path='/v3/fhir/Coverage', method='GET')
        has_match = has_matching_protected_resource(self.protected_resources, request)

        assert has_match is True


[['GET', '/v[123]/fhir/Coverage[/?].*$'], ['GET', '/v[123]/fhir/Coverage[/]?$']]
[['GET', '/v[123]/fhir/Coverage[/?].*$']]
