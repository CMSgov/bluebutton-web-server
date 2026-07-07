import json
from http import HTTPStatus

import pytest
from django.test.client import Client
from django.urls import reverse
from httmock import HTTMock, all_requests
from waffle.testutils import override_switch

from apps.integration_tests.constants import MESSAGE_NO_PERMISSION

client = Client()


@override_switch('v3_endpoints', active=True)
@override_switch('require-scopes', active=True)
@override_switch('enable_auditevents', active=True)
def test_audit_event_call_without_audit_event_scope(basic_user, get_access_token):
    """Try to make an audit_event call without having the appropriate scope, confirm a 403 is returned

    Args:
        basic_user: Fixture for a basic_user
        get_access_token: Fixture to create an access token
    """
    user = basic_user()
    access_token = get_access_token(
        user.username, 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs profile'
    )

    response = client.get(
        reverse('bb_oauth_fhir_audit_event'),
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()['detail'] == MESSAGE_NO_PERMISSION


@override_switch('v3_endpoints', active=True)
@override_switch('require-scopes', active=True)
def test_v2_audit_event_call_confirm_not_found(basic_user, get_access_token):
    """Try to make a v2 audit event call, which BlueButton does not support. Confirm a 404 is returned

    Args:
        basic_user: Fixture for a basic_user
        get_access_token: Fixture to create an access token
    """
    user = basic_user()
    access_token = get_access_token(
        user.username, 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs profile'
    )

    response = client.get(
        '/v2/fhir/AuditEvent',
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


@override_switch('v3_endpoints', active=False)
@override_switch('require-scopes', active=True)
def test_audit_event_call_without_v3_endpoints_enabled(basic_user, get_access_token):
    """Try to make a v3 audit event call, with the v3_endpoints flag set to False. Confirm a 404 is returned.

    Args:
        basic_user: Fixture for a basic_user
        get_access_token: Fixture to create an access token
    """
    user = basic_user()
    access_token = get_access_token(
        user.username, 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs profile'
    )

    response = client.get(
        reverse('bb_oauth_fhir_audit_event'),
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


@override_switch('v3_endpoints', active=True)
@override_switch('require-scopes', active=True)
@override_switch('enable_auditevents', active=True)
def test_mock_successful_audit_event_call(basic_user, get_access_token, create_capability):
    """With a mock AuditEvent response, confirm we get the expected resources back and are able
    to parse the response as expected

    Args:
        basic_user: Fixture for a basic_user
        get_access_token: Fixture to create an access token
        create_capability: Fixture to create a capabilities_protectedcapability record
    """
    user = basic_user(
        username='damon',
        first_name='Damon',
        last_name='Mychart',
        fhir_id_v2='custom_fhir_id',
        fhir_id_v3='-502120048',
    )
    access_token = get_access_token(
        user.username,
        'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs patient/AuditEvent.rs',
    )
    create_capability('patient/AuditEvent.rs', [['GET', '/v[3]/fhir/AuditEvent[/]?$']])

    with open('apps/fhir/bluebutton/tests/sample_responses/audit_event_response.json') as f:
        audit_event_bundle = json.load(f)

    @all_requests
    def catchall(url, req):
        return {'status_code': HTTPStatus.OK, 'content': audit_event_bundle}

    with HTTMock(catchall):
        response = client.get(reverse('bb_oauth_fhir_audit_event'), Authorization='Bearer %s' % (access_token))

    json_response = response.json()
    audit_event_resource = json_response.get('entry')[0].get('resource')

    assert response.status_code == HTTPStatus.OK
    assert json_response.get('resourceType') == 'Bundle'
    assert audit_event_resource.get('resourceType') == 'AuditEvent'
    assert audit_event_resource.get('id') == '-502120048-20260706192218527441255'


@pytest.mark.integration
@override_switch('v3_endpoints', active=True)
@override_switch('require-scopes', active=True)
@override_switch('enable_auditevents', active=True)
def test_successful_audit_event_call(basic_user, get_access_token, create_capability):
    """Make an actual live call to BFD for the AuditEvent endpoint that returns a 200

    Args:
        basic_user: Fixture for a basic_user
        get_access_token: Fixture to create an access token
        create_capability: Fixture to create a capabilities_protectedcapability record
    """
    user = basic_user()
    access_token = get_access_token(
        user.username,
        'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs patient/AuditEvent.rs',
    )
    create_capability('patient/AuditEvent.rs', [['GET', '/v[3]/fhir/AuditEvent[/]?$']])

    response = client.get(
        reverse('bb_oauth_fhir_audit_event'),
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['resourceType'] == 'Bundle'
