import json
from http import HTTPStatus

import pytest
from django.test.client import Client
from django.urls import reverse
from httmock import HTTMock, all_requests
from waffle.testutils import override_switch

from apps.integration_tests.constants import MESSAGE_NO_PERMISSION

client = Client()


@override_switch('v3_endpoints', True)
@override_switch('require-scopes', True)
def test_audit_event_call_without_audit_event_scope(basic_user, get_access_token):
    user = basic_user()
    access_token = get_access_token(
        user.username, 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs profile'
    )

    response = client.get(
        reverse('bb_oauth_fhir_audit_event'),
        kwargs={'entity': 'test'},
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()['detail'] == MESSAGE_NO_PERMISSION


@override_switch('v3_endpoints', True)
@override_switch('require-scopes', True)
def test_v2_audit_event_call_confirm_not_found(basic_user, get_access_token):
    user = basic_user()
    access_token = get_access_token(
        user.username, 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs profile'
    )

    response = client.get(
        '/v2/fhir/AuditEvent',
        kwargs={'entity': 'test'},
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


@override_switch('v3_endpoints', False)
@override_switch('require-scopes', True)
def test_audit_event_call_without_v3_endpoints_enabled(basic_user, get_access_token):
    user = basic_user()
    access_token = get_access_token(
        user.username, 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs profile'
    )

    response = client.get(
        reverse('bb_oauth_fhir_audit_event'),
        kwargs={'entity': 'test'},
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


@override_switch('v3_endpoints', True)
@override_switch('require-scopes', True)
def test_mock_successful_audit_event_call(basic_user, get_access_token, create_capability):
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
        response = client.get(
            reverse('bb_oauth_fhir_audit_event'), kwargs={'entity': 'test'}, Authorization='Bearer %s' % (access_token)
        )

    json_response = response.json()
    audit_event_resource = json_response.get('entry')[0].get('resource')

    assert response.status_code == HTTPStatus.OK
    assert json_response.get('resourceType') == 'Bundle'
    assert audit_event_resource.get('resourceType') == 'AuditEvent'
    assert audit_event_resource.get('id') == '-502120048-20260706192218527441255'


@pytest.mark.integration
@override_switch('v3_endpoints', True)
@override_switch('require-scopes', True)
def test_successful_audit_event_call(basic_user, get_access_token, create_capability):
    user = basic_user()
    access_token = get_access_token(
        user.username,
        'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs patient/AuditEvent.rs',
    )
    create_capability('patient/AuditEvent.rs', [['GET', '/v[3]/fhir/AuditEvent[/]?$']])

    response = client.get(
        reverse('bb_oauth_fhir_audit_event'),
        kwargs={'entity': 'test'},
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['resourceType'] == 'Bundle'
