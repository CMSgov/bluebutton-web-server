import json
import secrets
from datetime import datetime, timedelta

import pytest
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
    """A basic user with default test values."""

    test_hicn_hash = '96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7'
    test_mbi = '1SA0A00AA00'

    if User.objects.filter(username='john').exists():
        return User.objects.get(username='john')

    user = User.objects.create_user(
        username='john',
        password='123456',
        first_name='John',
        last_name='Smith',
        email='john.smith@test.notanagency.gov',
    )

    Crosswalk.objects.create(
        user=user,
        fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2,
        fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3,
        user_hicn_hash=test_hicn_hash,
        user_mbi=test_mbi,
    )

    return user


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
