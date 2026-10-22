from http import HTTPStatus

import pytest
from django.test.client import Client
from django.urls import reverse
from waffle.testutils import override_switch
from unittest.mock import patch, MagicMock

from apps.constants import SAMPLE_CAN_USER_FHIR_ID_V3

client = Client()

@pytest.mark.integration
@override_switch('v3_endpoints', active=True)
@override_switch('require-scopes', active=True)
@override_switch('enable_auditevents', active=True)
@patch('apps.fhir.views.generic.requests.get')
def test_json_decode_error(basic_user, get_access_token, create_capability):
    """Make an actual live call to BFD for the patient endpoint that returns a JSONDecodeError

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
        fhir_id_v3=SAMPLE_CAN_USER_FHIR_ID_V3,
    )
    access_token = get_access_token(
        user.username,
        'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs patient/AuditEvent.rs',
    )
    create_capability('patient/AuditEvent.rs', [['GET', '/v[3]/fhir/patient[/]?$']])

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = "mocked_payload"
    mock_get.return_value = mock_response

    response = client.get(
        reverse('bb_oauth_fhir_patient_read_or_update_or_delete'),
        Authorization='Bearer %s' % (access_token),
    )

    assert response.status_code == HTTPStatus.Bad_Gateway

