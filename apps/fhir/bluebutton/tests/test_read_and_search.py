import copy
import json
from http import HTTPStatus
from unittest.mock import patch
from urllib.parse import unquote

import pytest
from django.core.cache import cache
from django.test import RequestFactory
from django.test.client import Client
from django.urls import reverse
from httmock import HTTMock, all_requests, urlmatch
from oauth2_provider.models import get_access_token_model
from waffle.testutils import override_switch

import apps.fhir.bluebutton.utils
from apps.constants import APPLICATION_TEMPORARILY_INACTIVE

# Get the pre-defined Conformance statement
from apps.fhir.bluebutton.tests.data_conformance import CONFORMANCE
from apps.fhir.bluebutton.views.home import conformance_filter
from apps.fhir.constants import (
    READ_UPDATE_DELETE_COVERAGE_URLS,
    READ_UPDATE_DELETE_EOB_URLS,
    READ_UPDATE_DELETE_PATIENT_URLS,
    SEARCH_EOB_URLS,
    SEARCH_PATIENT_URLS,
)
from apps.mymedicare_cb.tests.responses import patient_response
from apps.test import BaseApiTest
from apps.versions import Versions

AccessToken = get_access_token_model()
client = Client()

SAMPLE_FHIR_ID_BY_VERSION = Versions.sample_fhir_id_by_version()
FHIR_URL_BY_VERSION = Versions.fhir_url_by_version()
VERSIONS = Versions.supported_versions()


@pytest.fixture
def create_token(db):
    """Factory fixture wrapping BaseApiTest.create_token (user/app/capabilities/token setup)."""
    helper = BaseApiTest()
    helper.read_capability = helper._create_capability('Read', [])
    helper.write_capability = helper._create_capability('Write', [])
    return helper.create_token


@pytest.fixture
def sample_fhir_id(version):
    """The version-specific sample FHIR id, matching the crosswalk populated by first_access_token."""
    return SAMPLE_FHIR_ID_BY_VERSION[version]


@pytest.fixture
def first_access_token(create_token):
    """A standard 'John Smith' access token with both v2 and v3 crosswalk ids populated."""
    return create_token(
        'John',
        'Smith',
        fhir_id_v2=SAMPLE_FHIR_ID_BY_VERSION[Versions.V2],
        fhir_id_v3=SAMPLE_FHIR_ID_BY_VERSION[Versions.V3],
    )


def get_expected_read_request(version: int, sample_fhir_id: str):
    fhir_url = FHIR_URL_BY_VERSION[version]
    return {
        'method': 'GET',
        'url': f'{fhir_url}/v{version}/fhir/Patient/{sample_fhir_id}/?_format=application/fhir+json&_id={sample_fhir_id}',
        'headers': {
            # 'User-Agent': 'python-requests/2.20.0',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'BlueButton-OriginalQueryCounter': '1',
            'BlueButton-BeneficiaryId': f'patientId:{sample_fhir_id}',
            'BlueButton-Application': 'John_Smith_test',
            'X-Forwarded-For': '127.0.0.1',
            'keep-alive': 'timeout=120, max=10',
            'BlueButton-OriginalUrl': f'/v{version}/fhir/Patient/{sample_fhir_id}',
            'BlueButton-BackendCall': (f'{fhir_url}/v{version}/fhir/Patient/{sample_fhir_id}/'),
        },
    }


def get_expected_request(version, sample_fhir_id):
    fhir_url = FHIR_URL_BY_VERSION[version]
    return {
        'method': 'GET',
        'url': (f'{fhir_url}/v{version}/fhir/Patient/?_format=application%2Fjson%2Bfhir&_id={sample_fhir_id}'),
        'headers': {
            # 'User-Agent': 'python-requests/2.20.0',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'BlueButton-OriginalQueryCounter': '1',
            'BlueButton-BeneficiaryId': f'patientId:{sample_fhir_id}',
            'BlueButton-Application': 'John_Smith_test',
            'X-Forwarded-For': '127.0.0.1',
            'keep-alive': 'timeout=120, max=10',
            'BlueButton-OriginalUrl': f'/v{version}/fhir/Patient',
            'BlueButton-BackendCall': f'{fhir_url}/v{version}/fhir/Patient/',
        },
    }


@patch('apps.fhir.bluebutton.utils.requests')
def test_fhir_bluebutton_read_conformance_testcase(mock_requests):
    """Checking Conformance

    The @patch replaces the call to requests with mock_requests
    """
    factory = RequestFactory()
    call_to = '/bluebutton/fhir/v1/metadata'
    request = factory.get(call_to)

    # Now we can setup the responses we want to the call
    mock_requests.get.return_value.status_code = 200
    mock_requests.get.return_value.content = CONFORMANCE

    # Make the call to request_call which uses requests.get
    # patch will intercept the call to requests.get and
    # return the pre-defined values
    result = apps.fhir.bluebutton.utils.request_call(request, call_to, crosswalk=None)

    # Test for a match
    assert result._response.content == CONFORMANCE


def test_fhir_conformance_filter():
    """Check filtering of Conformance Statement"""

    conform_out = json.loads(CONFORMANCE)
    result = conformance_filter(conform_out)

    assert 'vision' not in result['rest'][0]['resource']


# _lower_dict :: dict -> dictionary
# Lowercases the keys and values in a dictionary.
# Also forces everything to a string.
# This is to then compare the dictionaries as sets.
def _lower_dict(d):
    lower_d = {}
    for k, v in d.items():
        lower_d[str(k).lower()] = str(v).lower()
    return lower_d


# _contains_subset :: dict, dict -> bool
# Asks if d1 contains d1 as a subset.


def _contains_subset(d1, d2) -> bool:
    d1_set = set(_lower_dict(d1).keys())
    d2_set = set(_lower_dict(d2).keys())
    res = d1_set.issubset(d2_set)
    return res


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
@patch('apps.dot_ext.throttling.TokenRateThrottle.get_rate')
def test_read_throttle(mock_rates, version, sample_fhir_id, first_access_token, create_token):
    cache.clear()
    mock_rates.return_value = '1/day'
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/Patient.read'
    ac.save()

    @all_requests
    def catchall(url, req):
        return {
            'status_code': 200,
            'content': {
                'resourceType': 'Patient',
                'id': sample_fhir_id,
                'extension': [
                    {
                        'url': 'https://bluebutton.cms.gov/resources/variables/race',
                        'valueCoding': {
                            'system': 'https://bluebutton.cms.gov/resources/variables/race',
                            'code': '1',
                            'display': 'White',
                        },
                    }
                ],
                'identifier': [
                    {
                        'system': 'https://bluebutton.cms.gov/resources/variables/bene_id',
                        'value': sample_fhir_id,
                    },
                    {
                        'system': 'https://bluebutton.cms.gov/resources/identifier/hicn-hash',
                        'value': '2025fbc612a884853f0c245e686780bf748e5652360ecd7430575491f4e018c5',
                    },
                ],
                'name': [{'use': 'usual', 'family': 'Doe', 'given': ['Jane', 'X']}],
                'gender': 'unknown',
                'birthDate': '2014-06-01',
                'address': [{'district': '999', 'state': '15', 'postalCode': '99999'}],
            },
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': sample_fhir_id}),
            Authorization='Bearer %s' % (first_access_token),
        )

        assert response.status_code == 200

        assert response.has_header('X-RateLimit-Limit')
        assert response.get('X-RateLimit-Limit') == '1'

        assert response.has_header('X-RateLimit-Remaining')
        assert response.get('X-RateLimit-Remaining') == '0'

        assert response.has_header('X-RateLimit-Reset')
        # 86400.0 is 24 hours
        assert response.get('X-RateLimit-Reset') == '86400.0'

        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': sample_fhir_id}),
            Authorization='Bearer %s' % (first_access_token),
        )

        assert response.status_code == 429
        # Assert that the proper headers are in place
        assert response.has_header('X-RateLimit-Limit')
        assert response.get('X-RateLimit-Limit') == '1'

        assert response.has_header('X-RateLimit-Remaining')
        assert response.get('X-RateLimit-Remaining') == '0'

        assert response.has_header('X-RateLimit-Reset')
        # 86400.0 is 24 hours
        assert float(response.get('X-RateLimit-Reset')) < 86400.0

        assert response.has_header('Retry-After')
        assert response.get('Retry-After') == '86400'

        # Assert that the search endpoint is also ratelimited
        response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization='Bearer %s' % (first_access_token))

        assert response.status_code == 429

        # Assert that another token is not rate limited
        second_access_token = create_token(
            'Bob',
            'Bobbington',
            fhir_id_v2=SAMPLE_FHIR_ID_BY_VERSION[Versions.V2],
            fhir_id_v3=SAMPLE_FHIR_ID_BY_VERSION[Versions.V3],
        )
        assert second_access_token != first_access_token

        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': sample_fhir_id}),
            Authorization='Bearer %s' % (second_access_token),
        )

        assert response.status_code == 200


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_search_request(version, sample_fhir_id, first_access_token):
    # The returned patient id must match the crosswalk fhir id for this version
    expected_response = copy.deepcopy(patient_response)
    expected_response['entry'][0]['resource']['id'] = sample_fhir_id
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/Patient.read'
    ac.save()
    expected_request = get_expected_request(version, sample_fhir_id)

    @all_requests
    def catchall(url, req):
        assert f'{FHIR_URL_BY_VERSION[version]}/v{version}/fhir/Patient/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url
        assert f'_id={sample_fhir_id}' in req.url
        assert '_count=5' in req.url
        assert 'hello' not in req.url
        assert expected_request['method'] == req.method
        assert _contains_subset(expected_request['headers'], req.headers)

        return {
            'status_code': 200,
            # TODO replace this with true backend response, this has been post processed
            'content': expected_response,
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_PATIENT_URLS[version]), {'count': 5}, Authorization='Bearer %s' % (first_access_token)
        )

        assert response.status_code == 200
        # asserts no significant transformation
        assert response.json()['entry'] == expected_response['entry']
        assert len(response.json()['link']) > 0
        assert '_count=5' in response.json()['link'][0]['url']


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_search_request_unauthorized(version, db):
    response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization='Bearer bogus')

    assert response.status_code == 401


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_search_request_access_token_query_param(version, first_access_token):
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/Patient.read'
    ac.save()
    url = reverse(SEARCH_PATIENT_URLS[version])
    url += '?access_token=%s' % (first_access_token)
    response = client.get(url, Authorization='Bearer %s' % (first_access_token))

    assert response.status_code == 400
    content = json.loads(response.content.decode('utf-8'))
    assert content['detail'] == (
        'Using the access token in the query parameters is not supported. Use the Authorization header instead'
    )


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_search_request_not_found(version, sample_fhir_id, first_access_token):
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/Patient.read'
    ac.save()
    expected_request = get_expected_request(version, sample_fhir_id)

    @all_requests
    def catchall(url, req):
        assert f'{FHIR_URL_BY_VERSION[version]}/v{version}/fhir/Patient/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url
        assert f'_id={sample_fhir_id}' in req.url
        assert expected_request['method'] == req.method
        assert _contains_subset(expected_request['headers'], req.headers)

        return {
            'status_code': 404,
            'content': {},
        }

    with HTTMock(catchall):
        response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization='Bearer %s' % (first_access_token))

        assert response.status_code == 404


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_search_emptyset(version, first_access_token):
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/ExplanationOfBenefit.read'
    ac.save()

    @all_requests
    def catchall(url, req):
        return {
            'status_code': 200,
            'content': {
                'resourceType': 'Bundle',
                'id': '4b74b5b0-f324-41cb-85db-f8d527f79128',
                'meta': {'lastUpdated': '2018-05-15T14:01:58.603+00:00'},
                'type': 'searchset',
                'link': [
                    {
                        'relation': 'self',
                        'url': f'http://hapi.fhir.org/v{version}/fhir/ExplanationOfBenefit?_pretty=true&patient=1234',
                    },
                ],
            },
        }

    with HTTMock(catchall):
        response = client.get(reverse(SEARCH_EOB_URLS[version]), Authorization='Bearer %s' % (first_access_token))

        assert response.status_code == 200


@pytest.mark.parametrize('bfd_status_code', (500, 400))
@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_search_request_failed(version, bfd_status_code, sample_fhir_id, first_access_token):
    # BB2-1965 for 400 or 500 BFD response compatibility.
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/Patient.read'
    ac.save()
    expected_request = get_expected_request(version, sample_fhir_id)

    @all_requests
    def catchall(url, req):
        assert f'{FHIR_URL_BY_VERSION[version]}/v{version}/fhir/Patient/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url
        assert f'_id={sample_fhir_id}' in req.url
        assert expected_request['method'] == req.method
        assert _contains_subset(expected_request['headers'], req.headers)

        return {
            'status_code': bfd_status_code,
            'content': {},
        }

    with HTTMock(catchall):
        response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization='Bearer %s' % (first_access_token))

        assert response.status_code == 502


@pytest.mark.parametrize('bfd_status_code', (500, 400))
@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_search_request_failed_no_fhir_id_match(version, bfd_status_code, sample_fhir_id, first_access_token):
    # BB2-1965 for 400 or 500 BFD response compatibility.
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/Patient.read'
    ac.save()
    expected_request = get_expected_request(version, sample_fhir_id)

    @urlmatch(
        query=r'.*identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C139e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130.*'
    )
    def fhir_request(url, req):
        return {
            'status_code': 200,
            'content': {
                'entry': [
                    {
                        'resource': {
                            'id': sample_fhir_id,
                        },
                    }
                ],
            },
        }

    @all_requests
    def catchall(url, req):
        assert f'{FHIR_URL_BY_VERSION[version]}/v{version}/fhir/Patient/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url
        assert f'_id={sample_fhir_id}' in req.url
        assert expected_request['method'] == req.method
        assert _contains_subset(expected_request['headers'], req.headers)

        return {
            'status_code': bfd_status_code,
            'content': {},
        }

    with HTTMock(fhir_request, catchall):
        response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization='Bearer %s' % (first_access_token))

        assert response.status_code == 502


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_search_parameters_request(version, sample_fhir_id, first_access_token):
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/ExplanationOfBenefit.read'
    ac.save()

    @all_requests
    def catchall(url, req):
        assert f'{FHIR_URL_BY_VERSION[version]}/v{version}/fhir/ExplanationOfBenefit/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url

        return {
            'status_code': 200,
            'content': {
                'resourceType': 'ExplanationOfBenefit',
                'patient': {
                    'reference': f'stuff/{sample_fhir_id}',
                },
            },
        }

    # Test _lastUpdated with valid parameter starting with 'lt'
    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_EOB_URLS[version]),
            {'_lastUpdated': 'lt2019-11-22T14:00:00-05:00'},
            Authorization='Bearer %s' % (first_access_token),
        )
        assert response.status_code == 200

    # Test _lastUpdated with invalid parameter starting with 'zz'
    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_EOB_URLS[version]),
            {'_lastUpdated': 'zz2020-11-22T14:00:00-05:00'},
            Authorization='Bearer %s' % (first_access_token),
        )

        content = json.loads(response.content.decode('utf-8'))
        assert content['detail'] == 'the _lastUpdated operator is not valid'
        assert response.status_code == 400

    # Test type= with single valid value: 'pde'
    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_EOB_URLS[version]), {'type': 'pde'}, Authorization='Bearer %s' % (first_access_token)
        )
        assert response.status_code == 200

    # Test type= with multiple (all valid values)
    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_EOB_URLS[version]),
            {
                'type': 'carrier,'
                'pde,'
                'dme,'
                'hha,'
                'hospice,'
                'inpatient,'
                'outpatient,'
                'snf,'
                'https://bluebutton.cms.gov/resources/codesystem/eob-type|carrier,'
                'https://bluebutton.cms.gov/resources/codesystem/eob-type|pde,'
                'https://bluebutton.cms.gov/resources/codesystem/eob-type|dme,'
                'https://bluebutton.cms.gov/resources/codesystem/eob-type|hha,'
                'https://bluebutton.cms.gov/resources/codesystem/eob-type|hospice,'
                'https://bluebutton.cms.gov/resources/codesystem/eob-type|inpatient,'
                'https://bluebutton.cms.gov/resources/codesystem/eob-type|outpatient,'
                'https://bluebutton.cms.gov/resources/codesystem/eob-type|snf'
            },
            Authorization='Bearer %s' % (first_access_token),
        )
        assert response.status_code == 200

    # Test type= with an invalid type
    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_EOB_URLS[version]),
            {'type': 'carrier,INVALID-TYPE,dme,'},
            Authorization='Bearer %s' % (first_access_token),
        )

        content = json.loads(response.content.decode('utf-8'))
        assert content['detail'] == 'the type parameter value is not valid'
        assert response.status_code == 400


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_read_request_failed_no_fhir_id(version, sample_fhir_id, first_access_token):
    @urlmatch(
        query=r'.*identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C139e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130.*'
    )
    def fhir_request(url, req):
        return {
            'status_code': 200,
            'content': {
                'entry': [
                    {
                        'resource': {
                            'id': 20140000008324,
                        },
                    }
                ],
            },
        }

    @all_requests
    def catchall(url, req):
        return {
            'status_code': 200,
            'content': {},
        }

    with HTTMock(fhir_request, catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': sample_fhir_id}),
            Authorization='Bearer %s' % (first_access_token),
        )

        assert response.status_code == 403


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_read_request(version, sample_fhir_id, first_access_token):
    expected_request = get_expected_read_request(version, sample_fhir_id)

    @all_requests
    def catchall(url, req):
        assert expected_request['url'] == unquote(req.url)
        assert expected_request['method'] == req.method
        assert _contains_subset(expected_request['headers'], req.headers)

        return {
            'status_code': 200,
            'content': {
                'resourceType': 'Patient',
                'id': sample_fhir_id,
                'extension': [
                    {
                        'url': 'https://bluebutton.cms.gov/resources/variables/race',
                        'valueCoding': {
                            'system': 'https://bluebutton.cms.gov/resources/variables/race',
                            'code': '1',
                            'display': 'White',
                        },
                    }
                ],
                'identifier': [
                    {
                        'system': 'https://bluebutton.cms.gov/resources/variables/bene_id',
                        'value': sample_fhir_id,
                    },
                    {
                        'system': 'https://bluebutton.cms.gov/resources/identifier/hicn-hash',
                        'value': '2025fbc612a884853f0c245e686780bf748e5652360ecd7430575491f4e018c5',
                    },
                ],
                'name': [{'use': 'usual', 'family': 'Doe', 'given': ['Jane', 'X']}],
                'gender': 'unknown',
                'birthDate': '2014-06-01',
                'address': [{'district': '999', 'state': '15', 'postalCode': '99999'}],
            },
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': sample_fhir_id}),
            Authorization='Bearer %s' % (first_access_token),
        )

        assert response.status_code == 200


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_read_eob_request(version, sample_fhir_id, first_access_token):
    @all_requests
    def catchall(url, req):
        return {
            'status_code': 200,
            'content': {
                'resourceType': 'ExplanationOfBenefit',
                'patient': {
                    'reference': f'stuff/{sample_fhir_id}',
                },
            },
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_EOB_URLS[version], kwargs={'resource_id': 'eob_id'}),
            Authorization='Bearer %s' % (first_access_token),
        )

        assert response.status_code == 200


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_read_coverage_request(version, sample_fhir_id, first_access_token):
    @all_requests
    def catchall(url, req):
        return {
            'status_code': 200,
            'content': {
                'resourceType': 'Coverage',
                'beneficiary': {
                    'reference': f'stuff/{sample_fhir_id}',
                },
            },
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_COVERAGE_URLS[version], kwargs={'resource_id': 'coverage_id'}),
            Authorization='Bearer %s' % (first_access_token),
        )

        assert response.status_code == 200


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_application_first_last_active(version, sample_fhir_id, first_access_token):
    access_token_obj = AccessToken.objects.get(token=first_access_token)
    application = access_token_obj.application

    # Check that application last_active and first_active are not set (= None)
    assert application.first_active is None
    assert application.last_active is None

    @all_requests
    def catchall(url, req):
        return {
            'status_code': 200,
            'content': {
                'resourceType': 'Coverage',
                'beneficiary': {
                    'reference': f'stuff/{sample_fhir_id}',
                },
            },
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_COVERAGE_URLS[version], kwargs={'resource_id': 'coverage_id'}),
            Authorization='Bearer %s' % (first_access_token),
        )

        assert response.status_code == 200

    access_token_obj = AccessToken.objects.get(token=first_access_token)
    application = access_token_obj.application

    # Check that application last_active and first_active are set
    assert application.first_active is not None
    assert application.last_active is not None

    prev_first_active = application.first_active
    prev_last_active = application.last_active

    # 2nd resource call
    @all_requests
    def catchall(url, req):
        return {
            'status_code': 200,
            'content': {
                'resourceType': 'Coverage',
                'beneficiary': {
                    'reference': f'stuff/{sample_fhir_id}',
                },
            },
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_COVERAGE_URLS[version], kwargs={'resource_id': 'coverage_id'}),
            Authorization='Bearer %s' % (first_access_token),
        )

        assert response.status_code == 200

    access_token_obj = AccessToken.objects.get(token=first_access_token)
    application = access_token_obj.application

    # Check that application first_active is the same
    assert application.first_active == prev_first_active
    # Check that application last_active was updated
    assert application.last_active != prev_last_active


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_permission_deny_fhir_request_on_disabled_app_org(version, first_access_token):
    access_token_obj = AccessToken.objects.get(token=first_access_token)
    application = access_token_obj.application
    user = access_token_obj.user

    application.active = False
    application.save()

    assert application.active is False
    assert user.is_active is True

    @all_requests
    def catchall(url, req):
        return {
            'status_code': 200,
            'content': {
                'resourceType': 'Coverage',
                'beneficiary': {
                    'reference': f'stuff/{SAMPLE_FHIR_ID_BY_VERSION[Versions.V2]}',
                },
            },
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_COVERAGE_URLS[version], kwargs={'resource_id': 'coverage_id'}),
            Authorization='Bearer %s' % (first_access_token),
        )
        assert response.status_code == 401
        errStr = str(response.json().get('detail'))
        errwords = errStr.split()
        packedErrStr = '-'.join(errwords)
        msgwords = APPLICATION_TEMPORARILY_INACTIVE.split()
        packedMsg = '-'.join(msgwords)
        assert packedErrStr == packedMsg.format(application.name)

    # 2nd resource call
    @all_requests
    def catchall(url, req):
        return {
            'status_code': 200,
            'content': {
                'resourceType': 'Coverage',
                'beneficiary': {
                    'reference': f'stuff/{SAMPLE_FHIR_ID_BY_VERSION[Versions.V2]}',
                },
            },
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_COVERAGE_URLS[version], kwargs={'resource_id': 'coverage_id'}),
            Authorization='Bearer %s' % (first_access_token),
        )
        assert response.status_code == 401
        errStr = str(response.json().get('detail'))
        errwords = errStr.split()
        packedErrStr = '-'.join(errwords)
        msgwords = APPLICATION_TEMPORARILY_INACTIVE.split()
        packedMsg = '-'.join(msgwords)
        assert packedErrStr == packedMsg.format(application.name)
    # set app user back to active - not to affect subsequent tests
    application.active = True
    application.save()


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_read_on_different_fhir_id_than_associated_with_token(version, sample_fhir_id, first_access_token):
    """
    Confirm that a 404 is thrown when a Patient read request
    is attempted for a different fhir_id than the one associated
    with the current token.
    Note: The 404 is being mocked, as in these scenarios, we no longer
    ping BFD.
    """
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/Patient.read'
    ac.save()

    # Differs from the crosswalk's own fhir id for this version.
    non_token_fhir_id = str(int(sample_fhir_id) + 1)

    @all_requests
    def catchall(url, req):
        return {'status_code': HTTPStatus.NOT_FOUND, 'content': {}}

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': non_token_fhir_id}),
            Authorization='Bearer %s' % (first_access_token),
        )

    json_response = response.json()
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert json_response['detail'] == 'Not found.'


@pytest.mark.parametrize('version', VERSIONS)
@override_switch('v3_endpoints', active=True)
def test_read_on_fhir_id_that_does_not_exist(version, first_access_token):
    """
    Confirm that a 404 is thrown and we get a Not found message
    when a patient read is attempted on a non-existent fhir_id.
    Note: The 404 is being mocked, as in these scenarios, we no longer
    ping BFD.
    """
    ac = AccessToken.objects.get(token=first_access_token)
    ac.scope = 'patient/Patient.read'
    ac.save()

    non_token_fhir_id = '-99140000008326'

    @all_requests
    def catchall(url, req):
        return {'status_code': HTTPStatus.NOT_FOUND, 'content': {}}

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': non_token_fhir_id}),
            Authorization='Bearer %s' % (first_access_token),
        )

    json_response = response.json()
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert json_response['detail'] == 'Not found.'
