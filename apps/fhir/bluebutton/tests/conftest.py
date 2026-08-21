"""
Fixtures scoped to the FHIR BlueButton test package.

These live here rather than in the root conftest.py because only FHIR tests care
about API versions and version-specific sample FHIR ids.
"""

import pytest

from apps.versions import Versions


@pytest.fixture(params=Versions.supported_versions(), ids=lambda v: f'v{v}')
def version(request):
    """
    Parametrizes the requesting test across every supported API version.

    Requesting this fixture (directly, or transitively via sample_fhir_id or
    fhir_url) auto-parametrizes the test, so the
    @pytest.mark.parametrize('version', VERSIONS) decorator is no longer needed.

    To run against a subset, parametrize directly — direct parametrization takes
    precedence over a same-named fixture:

        @pytest.mark.parametrize('version', Versions.latest_versions())
        def test_v2_and_v3_only(version, sample_fhir_id):
            ...
    """
    return request.param


@pytest.fixture
def sample_fhir_id(version):
    """
    The version-specific sample FHIR id, matching the crosswalk that
    bene_access_token populates.
    """
    return Versions.sample_fhir_id_by_version()[version]


@pytest.fixture
def fhir_url(version):
    """The backend FHIR server base URL for this version (v3 differs from v1/v2)."""
    return Versions.fhir_url_by_version()[version]


@pytest.fixture
def bene_access_token(create_token):
    """
    Factory fixture for a beneficiary access token whose crosswalk carries both
    the v2 and v3 sample FHIR ids, so it resolves for any parametrized version.

    A factory rather than a plain value so tests can set the scope up front
    instead of minting a token and then mutating AccessToken.scope afterwards.

    Usage:
        def test_something(bene_access_token):
            token = bene_access_token(scope='patient/Patient.read')
            other = bene_access_token('Bob', 'Bobbington')
    """
    sample_fhir_ids = Versions.sample_fhir_id_by_version()

    def _bene_access_token(
        first_name: str = 'John',
        last_name: str = 'Smith',
        **kwargs,
    ) -> str:
        kwargs.setdefault('fhir_id_v2', sample_fhir_ids[Versions.V2])
        kwargs.setdefault('fhir_id_v3', sample_fhir_ids[Versions.V3])
        return create_token(first_name, last_name, **kwargs)

    return _bene_access_token
