
from django.conf import settings
from django.test.client import Client
from django.urls import reverse
from httmock import all_requests, HTTMock
from http import HTTPStatus
from oauth2_provider.models import get_access_token_model

from apps.test import BaseApiTest

# Get the pre-defined Conformance statement
from waffle.testutils import override_switch

AccessToken = get_access_token_model()

FHIR_ID_V2 = settings.DEFAULT_SAMPLE_FHIR_ID_V2

POSSIBLE_COVERAGE_SCOPES = ['patient/Coverage.read', 'patient/Coverage.rs', 'patient/Coverage.s']
POSSIBLE_PATIENT_SCOPES = ['patient/Patient.read', 'patient/Patient.rs', 'patient/Patient.r']


class InsuranceCardTest(BaseApiTest):
    TEST_TABLE = []
    # Add all of the passing combos. These should be 200s.
    for C in POSSIBLE_COVERAGE_SCOPES:
        for P in POSSIBLE_PATIENT_SCOPES:
            TEST_TABLE.append({'status': HTTPStatus.OK, 'scope': [C, P]})
    # If we only have one, those should fail with a 403.
    for C in POSSIBLE_COVERAGE_SCOPES:
        TEST_TABLE.append({'status': HTTPStatus.FORBIDDEN, 'scope': [C]})
    for P in POSSIBLE_PATIENT_SCOPES:
        TEST_TABLE.append({'status': HTTPStatus.FORBIDDEN, 'scope': [P]})

    def setUp(self):
        # create read and write capabilities
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])
        self.client = Client()

    @override_switch('v3_endpoints', active=True)
    def test_scope_combinations(self):
        for tt in InsuranceCardTest.TEST_TABLE:
            with self.subTest(tt=tt):
                token = self.create_token('Annie', 'User', fhir_id_v2=FHIR_ID_V2)
                ac = AccessToken.objects.get(token=token)
                ac.scope = " ".join(tt['scope'])
                ac.save()

                @all_requests
                def catchall(url, req):
                    return {
                        'status_code': 200,
                        'content': {
                            'doesnot': 'matter',
                        }
                    }
                with HTTMock(catchall):
                    response = self.client.get(
                        reverse('bb_oauth_fhir_dic_read'),
                        Authorization='Bearer %s' % (token)
                    )
                    self.assertEqual(response.status_code, tt['status'])
