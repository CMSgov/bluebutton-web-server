from http import HTTPStatus

from django.test import tag
from django.test.client import Client
from django.urls import reverse
from httmock import HTTMock, all_requests
from oauth2_provider.models import get_access_token_model

# Get the pre-defined Conformance statement
from waffle.testutils import override_switch

from apps.constants import (
    APPLICATION_DOES_NOT_HAVE_VALID_SCOPES,
    COVERAGE_SCOPE,
    DEFAULT_SAMPLE_FHIR_ID_V2,
    PATIENT_SCOPE,
)
from apps.dot_ext.models import Application, ProtectedCapability
from apps.test import BaseApiTest

AccessToken = get_access_token_model()

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
                token = self.create_token('Annie', 'User', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)
                ac = AccessToken.objects.get(token=token)
                ac.scope = ' '.join(tt['scope'])
                ac.save()

                @all_requests
                def catchall(url, req):
                    return {
                        'status_code': 200,
                        'content': {
                            'doesnot': 'matter',
                        },
                    }

                with HTTMock(catchall):
                    response = self.client.get(reverse('bb_oauth_fhir_dic_read'), Authorization='Bearer %s' % (token))
                    self.assertEqual(response.status_code, tt['status'])

    @tag('integration')
    @override_switch('v3_endpoints', active=True)
    def test_app_scope_permissions_no_patient_read_scope_returns_403(self):
        """
        Returns a 403 since the dic resource won't have a patient read scope and they are trying to make a dic call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # Remove the patient scope for that app and try to make a call
        application = Application.objects.get(name='John_Smith_test')
        patient_scope = ProtectedCapability.objects.get(slug=PATIENT_SCOPE)
        application.scope.remove(patient_scope)

        response = self.client.get(reverse('bb_oauth_fhir_dic_read'), Authorization=f'Bearer {first_access_token}')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()['detail'],
            APPLICATION_DOES_NOT_HAVE_VALID_SCOPES.format('John_Smith_test', 'any', 'digital insurance card'),
        )

    @tag('integration')
    @override_switch('v3_endpoints', active=True)
    def test_app_scope_permissions_no_coverage_search_scope_returns_403(self):
        """
        Returns a 403 since the dic resource won't have a coverage search scope and they are trying to make a dic call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # Remove the patient scope for that app and try to make a call
        application = Application.objects.get(name='John_Smith_test')
        coverage_scope = ProtectedCapability.objects.get(slug=COVERAGE_SCOPE)
        application.scope.remove(coverage_scope)

        response = self.client.get(reverse('bb_oauth_fhir_dic_read'), Authorization=f'Bearer {first_access_token}')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()['detail'],
            APPLICATION_DOES_NOT_HAVE_VALID_SCOPES.format('John_Smith_test', 'any', 'digital insurance card'),
        )

    @tag('integration')
    @override_switch('v3_endpoints', active=True)
    def test_app_scope_permissions_has_both_patient_read_and_coverage_search_scopes_returns_200(self):
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        response = self.client.get(reverse('bb_oauth_fhir_dic_read'), Authorization=f'Bearer {first_access_token}')
        self.assertEqual(response.status_code, 200)
