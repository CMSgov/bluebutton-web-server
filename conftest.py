import json
import secrets
from datetime import datetime, timedelta

import pytest
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.utils.text import slugify
from oauth2_provider.models import get_access_token_model

from apps.authorization.models import DataAccessGrant
from apps.capabilities.models import ProtectedCapability
from apps.constants import (
    COVERAGE_SCOPE,
    DEFAULT_SAMPLE_FHIR_ID_V2,
    DEFAULT_SAMPLE_FHIR_ID_V3,
    EOB_SCOPE,
    PATIENT_SCOPE,
)
from apps.dot_ext.models import Application
from apps.fhir.bluebutton.models import Crosswalk
from apps.versions import Versions

# The scope string BaseApiTest._get_access_token hardcoded. Kept as a constant so
# tests only spell out a scope when the scope is the thing under test.
DEFAULT_TOKEN_SCOPE = 'patient/Coverage.rs patient/Patient.rs patient/ExplanationOfBenefit.rs profile'

# Ignore specific test files during collection
collect_ignore = [
    'scripts/medicare-test-synth-logins/test_medicare_logins.py',
    'apps/integration_tests/logging_tests.py',
    'apps/integration_tests/selenium_accounts_tests.py',
    'apps/integration_tests/selenium_spanish_tests.py',
    'apps/integration_tests/selenium_tests.py',
]


@pytest.fixture
def basic_user(db):
    """
    Factory fixture that creates a User with associated Crosswalk data.
    Falls back to default test values if no arguments are provided.

    Usage:
        # Use all defaults
        def test_something(basic_user):
            user = basic_user()

        # Override specific values
        def test_something(basic_user):
            user = basic_user(
                username='jane',
                first_name='Jane',
                last_name='Doe',
                fhir_id_v2='custom_fhir_id',
            )
    """

    def _basic_user(
        username: str = 'john',
        password: str = '123456',
        first_name: str = 'John',
        last_name: str = 'Smith',
        email: str = None,
        fhir_id_v2: str = DEFAULT_SAMPLE_FHIR_ID_V2,
        fhir_id_v3: str = DEFAULT_SAMPLE_FHIR_ID_V3,
        hicn_hash: str = '96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7',
        mbi: str = '1SA0A00AA00',
    ):
        resolved_email = email or f'{first_name.lower()}.{last_name.lower()}@test.notanagency.gov'

        # Return existing user if already created
        if User.objects.filter(username=username).exists():
            return User.objects.get(username=username)

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=resolved_email,
        )

        Crosswalk.objects.create(
            user=user,
            fhir_id_v2=fhir_id_v2,
            fhir_id_v3=fhir_id_v3,
            user_hicn_hash=hicn_hash,
            user_mbi=mbi,
        )

        return user

    return _basic_user


@pytest.fixture
def get_access_token(db):
    """
    Factory fixture that creates an AccessToken and DataAccessGrant
    directly in the DB for a given username and application.
    Usage:
        def test_something(get_access_token):
            token = get_access_token('john', application=my_app)
    """

    def _get_access_token(
        username: str,
        scope: str = DEFAULT_TOKEN_SCOPE,
        application=None,
        **extra_fields,
    ):

        AccessToken = get_access_token_model()

        # Deliberately .get() and not get_or_create(): a missing user means the test
        # forgot to build one, and that should fail loudly here rather than silently
        # mint a token against an implicitly-created default user.
        user = User.objects.get(username=username)

        # Use provided application or get/create a default one
        resolved_application = (
            application
            or Application.objects.get_or_create(
                name='test',
                defaults={
                    'user': user,
                    'client_type': Application.CLIENT_CONFIDENTIAL,
                    'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
                },
            )[0]
        )

        # Create the AccessToken object directly in the DB
        access_token = AccessToken.objects.create(
            user=user,
            application=resolved_application,
            token=secrets.token_hex(32),
            expires=datetime.now() + timedelta(seconds=36000),
            # scope='patient/Coverage.rs patient/Patient.rs patient/ExplanationOfBenefit.rs profile',
            scope=scope,
            **extra_fields,
        )

        DataAccessGrant.objects.update_or_create(
            beneficiary=user,
            application=resolved_application,
        )

        return access_token.token

    return _get_access_token


@pytest.fixture
def create_capability(db):
    """
    Factory fixture that creates a ProtectedCapability instance
    that controls access for a set of URLs.
    Usage:
        def test_something(create_capability):
            capability = create_capability('My Capability', ['/api/v1/resource/'])
    """

    def _create_capability(
        name: str,
        urls: list,
        group=None,
        default: bool = True,
        slug: str = None,
    ):
        # Slug defaults to the title. Do NOT run slugify() unconditionally here:
        # scope-style names like 'patient/AuditEvent.rs' must survive verbatim,
        # since the slug is what dot_ext.scopes matches against. Pass slug=
        # explicitly for human-readable titles ('Read' -> 'read').
        resolved_slug = slug if slug is not None else name

        # Return existing capability if it already exists. Matched on slug rather
        # than title, because create_blue_button_scopes also guards on slug — this
        # keeps the two from creating duplicate rows sharing one slug.
        try:
            return ProtectedCapability.objects.get(slug=resolved_slug)
        except ProtectedCapability.DoesNotExist:
            pass

        # Create a default group if none provided
        resolved_group = group or Group.objects.get_or_create(name='test')[0]

        capability = ProtectedCapability.objects.create(
            default=default,
            title=name,
            slug=resolved_slug,
            protected_resources=json.dumps(urls),
            group=resolved_group,
        )
        return capability

    return _create_capability


@pytest.fixture
def create_application(db):
    """
    Factory fixture that creates an Application instance with a name,
    client_type, grant_type, and optional capability.
    The default client_type is APPLICATION.CLIENT_PUBLIC.
    The default grant_type is APPLICATION.GRANT_PASSWORD.
    Usage:
        def test_something(create_application):
            app = create_application('my_app')
    """

    def _create_application(
        name: str,
        client_type=None,
        grant_type=None,
        capability=None,
        user=None,
        data_access_type=None,
        **kwargs,
    ):

        client_type = client_type or Application.CLIENT_PUBLIC
        grant_type = grant_type or Application.GRANT_PASSWORD

        # Use provided user or get/create a default dev user
        dev_user = user or User.objects.get_or_create(username='dev', defaults={'password': '123456'})[0]

        application = Application.objects.create(
            name=name,
            user=dev_user,
            client_type=client_type,
            authorization_grant_type=grant_type,
            **kwargs,
        )

        # Set data access type if provided
        if data_access_type:
            application.data_access_type = data_access_type
            application.save()

        # Add capability if provided
        if capability:
            application.scope.add(capability)

        return application

    return _create_application


@pytest.fixture
def blue_button_scopes(db):
    """
    Loads the real BB2 protected capabilities via the create_blue_button_scopes
    management command and returns the patient/coverage/eob ones keyed by slug.

    Kept as its own fixture rather than folded into create_token because the
    command creates 17 ProtectedCapability rows (20 if enable_auditevents is enabled), and rows with default=True are
    available to EVERY application (see dot_ext.scopes.get_available_scopes,
    which ORs Q(default=True) with Q(application=application)). Tests that assert
    on scope enforcement should not pay that side effect unless they ask for it.

    Usage:
        def test_something(blue_button_scopes):
            patient_cap = blue_button_scopes[PATIENT_SCOPE]
    """
    call_command('create_blue_button_scopes')

    return {
        capability.slug: capability
        for capability in ProtectedCapability.objects.filter(
            slug__in=[PATIENT_SCOPE, COVERAGE_SCOPE, EOB_SCOPE],
        )
    }


@pytest.fixture
def create_token(
    basic_user,
    create_application,
    create_capability,
    get_access_token,
    blue_button_scopes,
):
    """
    Factory fixture producing a complete authorized setup: user + crosswalk +
    application + capabilities + access token. Returns the token string.

    This is the pytest-native replacement for BaseApiTest.create_token. It
    composes the narrower factories above rather than instantiating BaseApiTest
    outside the unittest lifecycle.

    Reach for get_access_token directly when you already have a user and only
    need a token; reach for this when you need the whole chain.

    Usage:
        def test_something(create_token):
            token = create_token()
            other = create_token('Bob', 'Bobbington')
    """

    def _create_token(
        first_name: str = 'John',
        last_name: str = 'Smith',
        fhir_id_v2: str = DEFAULT_SAMPLE_FHIR_ID_V2,
        fhir_id_v3: str = DEFAULT_SAMPLE_FHIR_ID_V3,
        scope: str = DEFAULT_TOKEN_SCOPE,
        **user_kwargs,
    ) -> str:
        # username matches BaseApiTest, which passed first_name through as the
        # username. Some log assertions elsewhere key off it.
        user = basic_user(
            username=first_name,
            first_name=first_name,
            last_name=last_name,
            fhir_id_v2=fhir_id_v2,
            fhir_id_v3=fhir_id_v3,
            **user_kwargs,
        )

        # The '{First}_{Last}_test' name is asserted on in the
        # BlueButton-Application request header. Do not "tidy" it.
        application = create_application(f'{first_name}_{last_name}_test', user=user)

        application.scope.add(
            *blue_button_scopes.values(),
            create_capability('Read', [], slug=slugify('Read')),
            create_capability('Write', [], slug=slugify('Write')),
        )

        return get_access_token(user.username, scope=scope, application=application)

    return _create_token


@pytest.fixture(params=Versions.supported_versions(), ids=lambda v: f'v{v}')
def version(request):
    """
    Parametrizes the requesting test across every supported API version.

    Requesting this fixture — directly, or transitively via sample_fhir_id,
    fhir_url or any fixture built on them — auto-parametrizes the test, so no
    @pytest.mark.parametrize('version', ...) decorator is needed.

    To run against a subset, parametrize directly; direct parametrization takes
    precedence over a same-named fixture:

        @pytest.mark.parametrize('version', Versions.latest_versions())
        def test_v2_and_v3_only(version):
            ...
    """
    return request.param


@pytest.fixture
def sample_fhir_id(version):
    """
    The version-specific sample FHIR id, matching the crosswalk that
    bene_access_token and create_token populate.
    """
    if version == Versions.V3:
        return DEFAULT_SAMPLE_FHIR_ID_V3
    return DEFAULT_SAMPLE_FHIR_ID_V2


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

    def _bene_access_token(
        first_name: str = 'John',
        last_name: str = 'Smith',
        **kwargs,
    ) -> str:
        kwargs.setdefault('fhir_id_v2', DEFAULT_SAMPLE_FHIR_ID_V2)
        kwargs.setdefault('fhir_id_v3', DEFAULT_SAMPLE_FHIR_ID_V3)
        return create_token(first_name, last_name, **kwargs)

    return _bene_access_token
