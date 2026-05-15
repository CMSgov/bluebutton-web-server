from types import SimpleNamespace

from django.test import TestCase

from apps.utils import is_valid_scope


class IsValidScopeTest(TestCase):
    def test_is_valid_scope_returns_false(self) -> bool:
        """
        Returns False since the app has EOB and Coverage scopes but is trying to make a Patient call.
        """
        scopes = [
            '[\n    [\n        "GET",\n        "/v[123]/fhir/ExplanationOfBenefit[/?].*$"\n    ],\n    [\n        "GET",\n        "/v[123]/fhir/ExplanationOfBenefit[/]?$"\n    ]\n]',
            '[\n    [\n        "GET",\n        "/v[123]/fhir/Coverage[/?].*$"\n    ],\n    [\n        "GET",\n        "/v[123]/fhir/Coverage[/]?$"\n    ]\n]',
        ]
        request = SimpleNamespace(path='/v3/fhir/Patient', method='GET')
        is_valid = is_valid_scope(scopes, request)

        assert is_valid is False

    def test_is_valid_scope_returns_true(self) -> bool:
        """
        Returns True since the app has EOB and Coverage scopes and is trying to make a Coverage call.
        """
        scopes = [
            '[\n    [\n        "GET",\n        "/v[123]/fhir/ExplanationOfBenefit[/?].*$"\n    ],\n    [\n        "GET",\n        "/v[123]/fhir/ExplanationOfBenefit[/]?$"\n    ]\n]',
            '[\n    [\n        "GET",\n        "/v[123]/fhir/Coverage[/?].*$"\n    ],\n    [\n        "GET",\n        "/v[123]/fhir/Coverage[/]?$"\n    ]\n]',
        ]
        request = SimpleNamespace(path='/v3/fhir/Coverage', method='GET')
        is_valid = is_valid_scope(scopes, request)

        assert is_valid is True
