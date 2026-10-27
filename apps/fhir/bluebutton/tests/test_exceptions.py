from http import HTTPStatus
from httmock import HTTMock, all_requests

import pytest
from django.test.client import Client
from django.urls import reverse
from waffle.testutils import override_switch

from apps.constants import SAMPLE_CAN_USER_FHIR_ID_V3

client = Client()

@pytest.mark.integration
@override_switch('v3_endpoints', active=True)
@override_switch('require-scopes', active=False)
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
        'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs patient/Search.rs',
    )
    create_capability('patient/Search.rs', [['GET', '/v[3]/fhir/Patient[/]?$']])

    text_string = "bad"
    byte_data = text_string.encode("utf-8")

    @all_requests
    def catchall(url, req):
        return {'status_code': HTTPStatus.INTERNAL_SERVER_ERROR, 'content': 'bad content', 'backend_response_text': 'bad content', 'backend_response': {'_content': byte_data}}

    with HTTMock(catchall):
        response = client.get(reverse('bb_oauth_fhir_patient_search'), Authorization='Bearer %s' % (access_token))

    assert response.status_code == HTTPStatus.BAD_GATEWAY

