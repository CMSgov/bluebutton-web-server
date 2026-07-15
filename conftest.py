import json
import secrets
from datetime import datetime, timedelta

import pytest

try:
    from django.contrib.auth.models import Group, User
    from oauth2_provider.models import get_access_token_model

    from apps.authorization.models import DataAccessGrant
    from apps.capabilities.models import ProtectedCapability
    from apps.constants import (
        DEFAULT_SAMPLE_FHIR_ID_V2,
        DEFAULT_SAMPLE_FHIR_ID_V3,
    )
    from apps.dot_ext.models import Application
    from apps.fhir.bluebutton.models import Crosswalk
except ModuleNotFoundError:
    pass

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
        scope: str,
        application=None,
        **extra_fields,
    ):

        AccessToken = get_access_token_model()

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
    ):
        # Return existing capability if it already exists
        try:
            return ProtectedCapability.objects.get(title=name)
        except ProtectedCapability.DoesNotExist:
            pass

        # Create a default group if none provided
        resolved_group = group or Group.objects.get_or_create(name='test')[0]

        capability = ProtectedCapability.objects.create(
            default=default,
            title=name,
            slug=name,
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
