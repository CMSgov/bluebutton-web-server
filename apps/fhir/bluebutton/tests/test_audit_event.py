from http import HTTPStatus

import pytest
from django.test.client import Client
from django.urls import reverse
from waffle.testutils import override_switch

from apps.integration_tests.constants import MESSAGE_NO_PERMISSION

pytestmark = pytest.mark.django_db


@pytest.mark.integration
@override_switch('v3_endpoints', True)
@override_switch('require-scopes', True)
def test_audit_event_call_without_audit_event_scope(basic_user, get_access_token):
    access_token = get_access_token(
        basic_user.username, 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs profile'
    )

    response = Client().get(
        reverse('bb_oauth_fhir_audit_event'),
        kwargs={'entity': 'test'},
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()['detail'] == MESSAGE_NO_PERMISSION


@pytest.mark.integration
@override_switch('v3_endpoints', False)
@override_switch('require-scopes', True)
def test_audit_event_call_without_v3_endpoints_enabled(basic_user, get_access_token):
    access_token = get_access_token(
        basic_user.username, 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs profile'
    )

    response = Client().get(
        reverse('bb_oauth_fhir_audit_event'),
        kwargs={'entity': 'test'},
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@override_switch('v3_endpoints', True)
@override_switch('require-scopes', True)
def test_successful_audit_event_call(basic_user, get_access_token, create_capability):
    access_token = get_access_token(
        basic_user.username,
        'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs patient/AuditEvent.rs',
    )
    create_capability('patient/AuditEvent.rs', [['GET', '/v[3]/fhir/AuditEvent[/]?$']])

    response = Client().get(
        reverse('bb_oauth_fhir_audit_event'),
        kwargs={'entity': 'test'},
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['resourceType'] == 'Bundle'
