import copy
import json
from http import HTTPStatus
from unittest.mock import patch
from urllib.parse import unquote

import pytest
from django.test import RequestFactory
from django.urls import reverse
from httmock import HTTMock, all_requests, urlmatch
from oauth2_provider.models import get_access_token_model
from waffle.testutils import override_switch

import apps.fhir.bluebutton.utils
from apps.constants import APPLICATION_TEMPORARILY_INACTIVE, DEFAULT_SAMPLE_FHIR_ID_V2

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

AccessToken = get_access_token_model()

# The scope granted to a token whose scope is not itself under test.
PATIENT_READ_SCOPE = 'patient/Patient.read'
EOB_READ_SCOPE = 'patient/ExplanationOfBenefit.read'


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def _lower_dict(d):
    """Lowercase keys and values, coercing to str, so dicts compare as sets."""
    return {str(k).lower(): str(v).lower() for k, v in d.items()}


def _contains_subset(d1, d2) -> bool:
    """Asks whether d1's keys are a subset of d2's keys."""
    return set(_lower_dict(d1).keys()).issubset(set(_lower_dict(d2).keys()))


# ---------------------------------------------------------------------------
# Expected-request builders
# ---------------------------------------------------------------------------


def _base_expected_headers(sample_fhir_id: str, original_url: str, backend_call: str) -> dict:
    return {
        # 'User-Agent': 'python-requests/2.20.0',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'BlueButton-OriginalQueryCounter': '1',
        'BlueButton-BeneficiaryId': f'patientId:{sample_fhir_id}',
        # Must match the '{First}_{Last}_test' application name built by the
        # create_token fixture in the root conftest.
        'BlueButton-Application': 'John_Smith_test',
        'X-Forwarded-For': '127.0.0.1',
        'keep-alive': 'timeout=120, max=10',
        'BlueButton-OriginalUrl': original_url,
        'BlueButton-BackendCall': backend_call,
    }


@pytest.fixture
def expected_read_request(version, sample_fhir_id, fhir_url):
    """The request we expect the backend to receive for a Patient read."""
    return {
        'method': 'GET',
        'url': (
            f'{fhir_url}/v{version}/fhir/Patient/{sample_fhir_id}/?_format=application/fhir+json&_id={sample_fhir_id}'
        ),
        'headers': _base_expected_headers(
            sample_fhir_id,
            original_url=f'/v{version}/fhir/Patient/{sample_fhir_id}',
            backend_call=f'{fhir_url}/v{version}/fhir/Patient/{sample_fhir_id}/',
        ),
    }


@pytest.fixture
def expected_search_request(version, sample_fhir_id, fhir_url):
    """The request we expect the backend to receive for a Patient search."""
    return {
        'method': 'GET',
        'url': (f'{fhir_url}/v{version}/fhir/Patient/?_format=application%2Fjson%2Bfhir&_id={sample_fhir_id}'),
        'headers': _base_expected_headers(
            sample_fhir_id,
            original_url=f'/v{version}/fhir/Patient',
            backend_call=f'{fhir_url}/v{version}/fhir/Patient/',
        ),
    }


# ---------------------------------------------------------------------------
# Conformance
# ---------------------------------------------------------------------------


@patch('apps.fhir.bluebutton.utils.requests')
def test_fhir_bluebutton_read_conformance_testcase(mock_requests):
    """Checking Conformance

    The @patch replaces the call to requests with mock_requests
    """
    factory = RequestFactory()
    call_to = '/bluebutton/fhir/v1/metadata'
    request = factory.get(call_to)

    # Now we can setup the responses we want to the call
    mock_requests.get.return_value.status_code = HTTPStatus.OK
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


# ---------------------------------------------------------------------------
# Throttling
# ---------------------------------------------------------------------------


@override_switch('v3_endpoints', active=True)
@patch('apps.dot_ext.throttling.TokenRateThrottle.get_rate')
def test_read_throttle(mock_rates, client, version, sample_fhir_id, bene_access_token):
    mock_rates.return_value = '1/day'

    access_token = bene_access_token(scope=PATIENT_READ_SCOPE)

    @all_requests
    def catchall(url, req):
        return {
            'status_code': HTTPStatus.OK,
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

    read_url = reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': sample_fhir_id})

    with HTTMock(catchall):
        response = client.get(read_url, Authorization=f'Bearer {access_token}')

        assert response.status_code == HTTPStatus.OK

        assert response.has_header('X-RateLimit-Limit')
        assert response.get('X-RateLimit-Limit') == '1'

        assert response.has_header('X-RateLimit-Remaining')
        assert response.get('X-RateLimit-Remaining') == '0'

        assert response.has_header('X-RateLimit-Reset')
        # 86400.0 is 24 hours
        assert response.get('X-RateLimit-Reset') == '86400.0'

        response = client.get(read_url, Authorization=f'Bearer {access_token}')

        assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
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
        response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization=f'Bearer {access_token}')

        assert response.status_code == HTTPStatus.FORBIDDEN

        # Assert that another token is not rate limited. Same factory, different
        # user, so no second fixture is needed.
        second_access_token = bene_access_token('Bob', 'Bobbington', scope=PATIENT_READ_SCOPE)
        assert second_access_token != access_token

        response = client.get(read_url, Authorization=f'Bearer {second_access_token}')

        assert response.status_code == HTTPStatus.OK


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@override_switch('v3_endpoints', active=True)
def test_search_request(client, version, sample_fhir_id, fhir_url, bene_access_token, expected_search_request):
    access_token = bene_access_token(scope=PATIENT_READ_SCOPE)

    # The returned patient id must match the crosswalk fhir id for this version
    expected_response = copy.deepcopy(patient_response)
    expected_response['entry'][0]['resource']['id'] = sample_fhir_id

    @all_requests
    def catchall(url, req):
        assert f'{fhir_url}/v{version}/fhir/Patient/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url
        assert f'_id={sample_fhir_id}' in req.url
        assert '_count=5' in req.url
        assert 'hello' not in req.url
        assert expected_search_request['method'] == req.method
        assert _contains_subset(expected_search_request['headers'], req.headers)

        return {
            'status_code': HTTPStatus.OK,
            'content': expected_response,
        }

    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_PATIENT_URLS[version]),
            {'count': 5},
            Authorization=f'Bearer {access_token}',
        )

        assert response.status_code == HTTPStatus.OK
        # asserts no significant transformation
        assert response.json()['entry'] == expected_response['entry']
        assert len(response.json()['link']) > 0
        assert '_count=5' in response.json()['link'][0]['url']


@override_switch('v3_endpoints', active=True)
def test_search_request_unauthorized(client, db, version):
    response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization='Bearer bogus')

    assert response.status_code == HTTPStatus.UNAUTHORIZED


@override_switch('v3_endpoints', active=True)
def test_search_request_access_token_query_param(client, version, bene_access_token):
    access_token = bene_access_token(scope=PATIENT_READ_SCOPE)

    url = reverse(SEARCH_PATIENT_URLS[version])
    url += f'?access_token={access_token}'
    response = client.get(url, Authorization=f'Bearer {access_token}')

    assert response.status_code == HTTPStatus.BAD_REQUEST
    content = json.loads(response.content.decode('utf-8'))
    assert content['detail'] == (
        'Using the access token in the query parameters is not supported. Use the Authorization header instead'
    )


@override_switch('v3_endpoints', active=True)
def test_search_request_not_found(
    client, version, sample_fhir_id, fhir_url, bene_access_token, expected_search_request
):
    access_token = bene_access_token(scope=PATIENT_READ_SCOPE)

    @all_requests
    def catchall(url, req):
        assert f'{fhir_url}/v{version}/fhir/Patient/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url
        assert f'_id={sample_fhir_id}' in req.url
        assert expected_search_request['method'] == req.method
        assert _contains_subset(expected_search_request['headers'], req.headers)

        return {
            'status_code': HTTPStatus.NOT_FOUND,
            'content': {},
        }

    with HTTMock(catchall):
        response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization=f'Bearer {access_token}')

        assert response.status_code == HTTPStatus.NOT_FOUND


@override_switch('v3_endpoints', active=True)
def test_search_emptyset(client, version, bene_access_token):
    access_token = bene_access_token(scope=EOB_READ_SCOPE)

    @all_requests
    def catchall(url, req):
        return {
            'status_code': HTTPStatus.OK,
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
        response = client.get(reverse(SEARCH_EOB_URLS[version]), Authorization=f'Bearer {access_token}')

        assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize('bfd_status_code', (500, 400))
@override_switch('v3_endpoints', active=True)
def test_search_request_failed(
    client,
    version,
    bfd_status_code,
    sample_fhir_id,
    fhir_url,
    bene_access_token,
    expected_search_request,
):
    # BB2-1965 for 400 or 500 BFD response compatibility.
    access_token = bene_access_token(scope=PATIENT_READ_SCOPE)

    @all_requests
    def catchall(url, req):
        assert f'{fhir_url}/v{version}/fhir/Patient/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url
        assert f'_id={sample_fhir_id}' in req.url
        assert expected_search_request['method'] == req.method
        assert _contains_subset(expected_search_request['headers'], req.headers)

        return {
            'status_code': bfd_status_code,
            'content': {},
        }

    with HTTMock(catchall):
        response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization=f'Bearer {access_token}')

        assert response.status_code == HTTPStatus.BAD_GATEWAY


@pytest.mark.parametrize('bfd_status_code', (500, 400))
@override_switch('v3_endpoints', active=True)
def test_search_request_failed_no_fhir_id_match(
    client,
    version,
    bfd_status_code,
    sample_fhir_id,
    fhir_url,
    bene_access_token,
    expected_search_request,
):
    # BB2-1965 for 400 or 500 BFD response compatibility.
    access_token = bene_access_token(scope=PATIENT_READ_SCOPE)

    @urlmatch(
        query=r'.*identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C139e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130.*'
    )
    def fhir_request(url, req):
        return {
            'status_code': HTTPStatus.OK,
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
        assert f'{fhir_url}/v{version}/fhir/Patient/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url
        assert f'_id={sample_fhir_id}' in req.url
        assert expected_search_request['method'] == req.method
        assert _contains_subset(expected_search_request['headers'], req.headers)

        return {
            'status_code': bfd_status_code,
            'content': {},
        }

    with HTTMock(fhir_request, catchall):
        response = client.get(reverse(SEARCH_PATIENT_URLS[version]), Authorization=f'Bearer {access_token}')

        assert response.status_code == HTTPStatus.BAD_GATEWAY


@override_switch('v3_endpoints', active=True)
def test_search_parameters_request(client, version, sample_fhir_id, fhir_url, bene_access_token):
    access_token = bene_access_token(scope=EOB_READ_SCOPE)

    @all_requests
    def catchall(url, req):
        assert f'{fhir_url}/v{version}/fhir/ExplanationOfBenefit/' in req.url
        assert '_format=application%2Ffhir%2Bjson' in req.url

        return {
            'status_code': HTTPStatus.OK,
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
            Authorization=f'Bearer {access_token}',
        )
        assert response.status_code == HTTPStatus.OK

    # Test _lastUpdated with invalid parameter starting with 'zz'
    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_EOB_URLS[version]),
            {'_lastUpdated': 'zz2020-11-22T14:00:00-05:00'},
            Authorization=f'Bearer {access_token}',
        )

        content = json.loads(response.content.decode('utf-8'))
        assert content['detail'] == 'the _lastUpdated operator is not valid'
        assert response.status_code == HTTPStatus.BAD_REQUEST

    # Test type= with single valid value: 'pde'
    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_EOB_URLS[version]),
            {'type': 'pde'},
            Authorization=f'Bearer {access_token}',
        )
        assert response.status_code == HTTPStatus.OK

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
            Authorization=f'Bearer {access_token}',
        )
        assert response.status_code == HTTPStatus.OK

    # Test type= with an invalid type
    with HTTMock(catchall):
        response = client.get(
            reverse(SEARCH_EOB_URLS[version]),
            {'type': 'carrier,INVALID-TYPE,dme,'},
            Authorization=f'Bearer {access_token}',
        )

        content = json.loads(response.content.decode('utf-8'))
        assert content['detail'] == 'the type parameter value is not valid'
        assert response.status_code == HTTPStatus.BAD_REQUEST


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


@override_switch('v3_endpoints', active=True)
def test_read_request_failed_no_fhir_id(client, version, sample_fhir_id, bene_access_token):
    # Note: no scope override — this exercises the default token scope.
    access_token = bene_access_token()

    @urlmatch(
        query=r'.*identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C139e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130.*'
    )
    def fhir_request(url, req):
        return {
            'status_code': HTTPStatus.OK,
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
            'status_code': HTTPStatus.OK,
            'content': {},
        }

    with HTTMock(fhir_request, catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': sample_fhir_id}),
            Authorization=f'Bearer {access_token}',
        )

        assert response.status_code == HTTPStatus.FORBIDDEN


@override_switch('v3_endpoints', active=True)
def test_read_request(client, version, sample_fhir_id, bene_access_token, expected_read_request):
    access_token = bene_access_token()

    @all_requests
    def catchall(url, req):
        assert expected_read_request['url'] == unquote(req.url)
        assert expected_read_request['method'] == req.method
        assert _contains_subset(expected_read_request['headers'], req.headers)

        return {
            'status_code': HTTPStatus.OK,
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
            Authorization=f'Bearer {access_token}',
        )

        assert response.status_code == HTTPStatus.OK


@override_switch('v3_endpoints', active=True)
def test_read_eob_request(client, version, sample_fhir_id, bene_access_token):
    access_token = bene_access_token()

    @all_requests
    def catchall(url, req):
        return {
            'status_code': HTTPStatus.OK,
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
            Authorization=f'Bearer {access_token}',
        )

        assert response.status_code == HTTPStatus.OK


@override_switch('v3_endpoints', active=True)
def test_read_coverage_request(client, version, sample_fhir_id, bene_access_token):
    access_token = bene_access_token()

    @all_requests
    def catchall(url, req):
        return {
            'status_code': HTTPStatus.OK,
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
            Authorization=f'Bearer {access_token}',
        )

        assert response.status_code == HTTPStatus.OK


# ---------------------------------------------------------------------------
# Application state. These two still need the AccessToken row itself (to reach
# .application / .user), so AccessToken.objects.get() stays here — it is not
# the scope-mutation boilerplate that the scope= argument replaced.
# ---------------------------------------------------------------------------


@override_switch('v3_endpoints', active=True)
def test_application_first_last_active(client, version, sample_fhir_id, bene_access_token):
    access_token = bene_access_token()

    access_token_obj = AccessToken.objects.get(token=access_token)
    application = access_token_obj.application

    # Check that application last_active and first_active are not set (= None)
    assert application.first_active is None
    assert application.last_active is None

    @all_requests
    def catchall(url, req):
        return {
            'status_code': HTTPStatus.OK,
            'content': {
                'resourceType': 'Coverage',
                'beneficiary': {
                    'reference': f'stuff/{sample_fhir_id}',
                },
            },
        }

    coverage_url = reverse(READ_UPDATE_DELETE_COVERAGE_URLS[version], kwargs={'resource_id': 'coverage_id'})

    with HTTMock(catchall):
        response = client.get(coverage_url, Authorization=f'Bearer {access_token}')

        assert response.status_code == HTTPStatus.OK

    access_token_obj = AccessToken.objects.get(token=access_token)
    application = access_token_obj.application

    # Check that application last_active and first_active are set
    assert application.first_active is not None
    assert application.last_active is not None

    prev_first_active = application.first_active
    prev_last_active = application.last_active

    # 2nd resource call — reuses the same mock, which was identical to the first.
    with HTTMock(catchall):
        response = client.get(coverage_url, Authorization=f'Bearer {access_token}')

        assert response.status_code == HTTPStatus.OK

    access_token_obj = AccessToken.objects.get(token=access_token)
    application = access_token_obj.application

    # Check that application first_active is the same
    assert application.first_active == prev_first_active
    # Check that application last_active was updated
    assert application.last_active != prev_last_active


@override_switch('v3_endpoints', active=True)
def test_permission_deny_fhir_request_on_disabled_app_org(client, version, bene_access_token):
    access_token = bene_access_token()

    access_token_obj = AccessToken.objects.get(token=access_token)
    application = access_token_obj.application
    user = access_token_obj.user

    application.active = False
    application.save()

    assert application.active is False
    assert user.is_active is True

    @all_requests
    def catchall(url, req):
        return {
            'status_code': HTTPStatus.OK,
            'content': {
                'resourceType': 'Coverage',
                'beneficiary': {
                    'reference': f'stuff/{DEFAULT_SAMPLE_FHIR_ID_V2}',
                },
            },
        }

    coverage_url = reverse(READ_UPDATE_DELETE_COVERAGE_URLS[version], kwargs={'resource_id': 'coverage_id'})

    def assert_inactive_application_response(response):
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        errStr = str(response.json().get('detail'))
        errwords = errStr.split()
        packedErrStr = '-'.join(errwords)
        msgwords = APPLICATION_TEMPORARILY_INACTIVE.split()
        packedMsg = '-'.join(msgwords)
        assert packedErrStr == packedMsg.format(application.name)

    with HTTMock(catchall):
        response = client.get(coverage_url, Authorization=f'Bearer {access_token}')
        assert_inactive_application_response(response)

    # 2nd resource call
    with HTTMock(catchall):
        response = client.get(coverage_url, Authorization=f'Bearer {access_token}')
        assert_inactive_application_response(response)

    # Set the app back to active so as not to affect subsequent tests. Strictly
    # unnecessary now that every test gets its own application from the factory
    # and the db fixture rolls back, but harmless and explicit.
    application.active = True
    application.save()


# ---------------------------------------------------------------------------
# fhir_id mismatch
# ---------------------------------------------------------------------------


@override_switch('v3_endpoints', active=True)
def test_read_on_different_fhir_id_than_associated_with_token(client, version, sample_fhir_id, bene_access_token):
    """
    Confirm that a 404 is thrown when a Patient read request
    is attempted for a different fhir_id than the one associated
    with the current token.
    Note: The 404 is being mocked, as in these scenarios, we no longer
    ping BFD.
    """
    access_token = bene_access_token(scope=PATIENT_READ_SCOPE)

    # Differs from the crosswalk's own fhir id for this version.
    non_token_fhir_id = str(int(sample_fhir_id) + 1)

    @all_requests
    def catchall(url, req):
        return {'status_code': HTTPStatus.NOT_FOUND, 'content': {}}

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': non_token_fhir_id}),
            Authorization=f'Bearer {access_token}',
        )

    json_response = response.json()
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert json_response['detail'] == 'Not found.'


@override_switch('v3_endpoints', active=True)
def test_read_on_fhir_id_that_does_not_exist(client, version, bene_access_token):
    """
    Confirm that a 404 is thrown and we get a Not found message
    when a patient read is attempted on a non-existent fhir_id.
    Note: The 404 is being mocked, as in these scenarios, we no longer
    ping BFD.
    """
    access_token = bene_access_token(scope=PATIENT_READ_SCOPE)

    non_token_fhir_id = '-99140000008326'

    @all_requests
    def catchall(url, req):
        return {'status_code': HTTPStatus.NOT_FOUND, 'content': {}}

    with HTTMock(catchall):
        response = client.get(
            reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': non_token_fhir_id}),
            Authorization=f'Bearer {access_token}',
        )

    json_response = response.json()
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert json_response['detail'] == 'Not found.'
