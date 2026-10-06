import importlib
import json
import logging
import os
from unittest.mock import patch

import pytest

from apps.constants import DEFAULT_SAMPLE_FHIR_ID_V2, DEFAULT_SAMPLE_FHIR_ID_V3
from apps.logging.constants import AUDIT_AUTHN_SLS_LOGGER, AUDIT_AUTHZ_TOKEN_LOGGER, AUDIT_HHS_AUTH_SERVER_REQ_LOGGER
from apps.logging.its_log_handler import ITSLogAPIHandler

log_handler = ITSLogAPIHandler()


def test_its_log_api_handler_absent_when_env_var_false():
    """Confirm that the its_log_api logging handler is not added to the base_local settings
    if ITS_LOG_API_ENABLED is false
    """
    with patch.dict(os.environ, {'ITS_LOG_API_ENABLED': 'False', 'TARGET_ENV': 'local'}):
        from hhs_oauth_server.settings import base_local  # adjust to your actual settings module

        assert 'its_log_api' not in base_local.LOGGING['loggers']['audit']['handlers']
        assert 'its_log_api' not in base_local.LOGGING['loggers']['hhs_server']['handlers']


def test_its_log_api_handler_present_when_env_var_true():
    """Confirm that the its_log_api logging handler is added to the base_local settings
    if ITS_LOG_API_ENABLED is true
    """
    with patch.dict(os.environ, {'ITS_LOG_API_ENABLED': 'True', 'TARGET_ENV': 'local'}):
        from hhs_oauth_server.settings import base_local

        importlib.reload(base_local)

        assert 'its_log_api' in base_local.LOGGING['handlers']
        assert 'its_log_api' in base_local.LOGGING['loggers']['audit']['handlers']
        assert 'its_log_api' in base_local.LOGGING['loggers']['hhs_server']['handlers']


def test_its_log_api_handler_absent_when_env_var_false_base_ec2():
    """Confirm that the its_log_api logging handler is not added to the base_local settings
    if ITS_LOG_API_ENABLED is false
    """
    with patch.dict(os.environ, {'ITS_LOG_API_ENABLED': 'False', 'TARGET_ENV': 'local'}):
        from hhs_oauth_server.settings import base_ec2  # adjust to your actual settings module

        assert 'its_log_api' not in base_ec2.LOGGING['loggers']['audit']['handlers']
        assert 'its_log_api' not in base_ec2.LOGGING['loggers']['hhs_server']['handlers']


def test_its_log_api_handler_present_when_env_var_true_base_ec2():
    """Confirm that the its_log_api logging handler is added to the base_local settings
    if ITS_LOG_API_ENABLED is true
    """
    with patch.dict(os.environ, {'ITS_LOG_API_ENABLED': 'True', 'TARGET_ENV': 'local'}):
        from hhs_oauth_server.settings import base_ec2

        importlib.reload(base_ec2)

        assert 'its_log_api' in base_ec2.LOGGING['handlers']
        assert 'its_log_api' in base_ec2.LOGGING['loggers']['audit']['handlers']
        assert 'its_log_api' in base_ec2.LOGGING['loggers']['hhs_server']['handlers']


@pytest.mark.parametrize(
    'log_type',
    [
        'fhir_post_fetch',
        'fhir_pre_fetch',
        'fhir_auth_post_fetch',
        'global_state_metrics',
        'global_state_metrics_per_app',
    ],
)
@patch('apps.logging.its_log_handler.ITSLogAPIHandler._post_to_api')
def test_log_not_posted_when_type_is_skippable(mock_post_to_api, log_type):
    """Confirm that we do not call the _post_to_api function if testclient is in the log.path

    Args:
        mock_post_to_api: Patch for the _post_to_api function
        log_type: The type of the log that was just output. We only post certain log types to the logging API
    """
    with patch.dict(os.environ, {'ITS_LOG_API_ENABLED': 'True'}):
        record = logging.makeLogRecord(
            {'name': 'test', 'level': logging.INFO, 'msg': 'Test connection established', 'type': log_type}
        )
        log_handler.emit(record)
        mock_post_to_api.assert_not_called()


@patch('apps.logging.its_log_handler.ITSLogAPIHandler._post_to_api')
def test_log_not_posted_when_testclient_in_path(mock_post_to_api):
    """Confirm that we do not call the _post_to_api function if testclient is in the log.path

    Args:
        mock_post_to_api: Patch for the _post_to_api function
    """
    with patch.dict(os.environ, {'ITS_LOG_API_ENABLED': 'True'}):
        record = logging.makeLogRecord(
            {
                'name': 'test',
                'level': logging.INFO,
                'msg': 'Test connection established',
                'type': 'Authorization',
                'path': '/testclient/',
            }
        )
        log_handler.emit(record)
        mock_post_to_api.assert_not_called()


@pytest.mark.parametrize(
    'log_msg, expected_result',
    [
        (True, {}),
        (
            '{"type": "request_response_middleware", "request_method": "GET", "path": "/testclient/PatientV2"}',
            {'type': 'request_response_middleware', 'request_method': 'GET', 'path': '/testclient/PatientV2'},
        ),
    ],
)
def test_parse_log_message(log_msg, expected_result):
    """Pass different values to the _parse_log_message function and ensure we get the expected result

    Args:
        log_msg: The log message being passed to _parse_log_message.
        expected_result: The expected result of _parse_log_message
    """
    record = logging.makeLogRecord(
        {
            'name': 'test',
            'level': logging.INFO,
            'msg': log_msg,
            'type': 'Authorization',
            'path': '/testclient/',
        }
    )
    result = log_handler._parse_log_message(record.__dict__)
    assert result == expected_result


@pytest.mark.parametrize(
    'log_message, expected_result',
    [
        (
            {
                'access_token_scopes': 'profile patient/Patient.rs patient/ExplanationOfBenefit.rs patient/Coverage.rs',
                'app_id': 35,
                'app_name': 'local logging',
                'app_require_demographic_scopes': True,
                'dev_id': 1,
                'dev_name': 'root',
                'fhir_id_v2': '-10000010284531',
                'fhir_id_v3': '-512738563',
                'fhir_resource_id': '6e9a3123-4a40-44f2-a195-e870a8801418',
                'fhir_resource_type': 'Bundle',
                'location': '',
                'path': '/v3/fhir/Patient/',
                'req_fhir_id_v2': '-10000010284531',
                'req_fhir_id_v3': '-512738563',
                'req_header_accept_encoding': 'gzip, deflate, br',
                'req_header_host': 'localhost:8000',
                'req_header_user_agent': 'PostmanRuntime/2.8.0',
                'request_method': 'GET',
                'response_code': 200,
                'type': 'request_response_middleware',
            },
            {
                'tags': [],
                'value': '{"app_id": 35, "app_name": "local logging", "fhir_id_v2": "-10000010284531", "fhir_id_v3": "-512738563", "path": "/v3/fhir/Patient/", "request_method": "GET", "response_code": 200, "type": "request_response_middleware"}',
                'type': 'text',
            },
        ),
        (
            {
                'access_token_hash': '',
                'app_id': 35,
                'app_name': 'local logging',
                'auth_grant_type': 'refresh_token',
                'dev_id': '',
                'dev_name': '',
                'elapsed': 1.2084159851074219,
                'end_time': 1790606675.534841,
                'location': '',
                'path': '/v3/o/token/',
                'req_client_id': None,
                'req_grant_type': 'refresh_token',
                'req_header_accept_encoding': 'gzip, deflate, br',
                'req_header_content_length': '166',
                'req_header_content_type': 'application/x-www-form-urlencoded',
                'req_header_host': 'localhost:8000',
                'req_header_user_agent': 'PostmanRuntime/7.56.1',
                'req_post_grant_type': 'refresh_token',
                'req_scope': 'profile%20patient%2FExplanationOfBenefit.rs%20patient%2FCoverage.rs%20patient%2FPatient.rs',
                'request_method': 'POST',
                'request_scheme': 'http',
                'request_uuid': '1f0fb7d4-bb4b-11f1-a1a1-9acbb38473dd',
                'resp_access_token_scopes': 'profile patient/Patient.rs patient/ExplanationOfBenefit.rs patient/Coverage.rs',
                'resp_app_id': 35,
                'resp_app_name': 'local logging',
                'resp_app_require_demographic_scopes': True,
                'resp_dev_id': 1,
                'resp_dev_name': 'root',
                'resp_expires_in': 3600,
                'resp_fhir_id': '-512738563',
                'resp_scope': 'profile patient/ExplanationOfBenefit.rs patient/Coverage.rs patient/Patient.rs',
                'resp_token_type': 'Bearer',
                'resp_user_id': 96,
                'response_code': 200,
                'type': 'request_response_middleware',
            },
            {
                'tags': [],
                'value': '{"app_id": 35, "app_name": "local logging", "auth_grant_type": "refresh_token", "path": "/v3/o/token/", "req_grant_type": "refresh_token", "request_method": "POST", "response_code": 200, "type": "request_response_middleware"}',
                'type': 'text',
            },
        ),
    ],
)
def test_build_payload(log_message, expected_result):
    """This test passes a sample log message to the _build_payload function, and confirms that the returned
    dictionary contains the field names that we expected

    Args:
        log_message: The log_message that is used to build the payload to the logging API
        expected_result: The expected result of the _build_payload function
    """
    result = log_handler._build_payload(log_message)
    assert result == expected_result


@pytest.mark.parametrize(
    'log_message, expected_fhir_id_v2, expected_fhir_id_v3',
    [
        (
            {
                'type': 'Authorization',
                'user': {
                    'crosswalk': {
                        'fhir_id_v2': DEFAULT_SAMPLE_FHIR_ID_V2,
                        'fhir_id_v3': DEFAULT_SAMPLE_FHIR_ID_V3,
                    }
                },
            },
            DEFAULT_SAMPLE_FHIR_ID_V2,
            DEFAULT_SAMPLE_FHIR_ID_V3,
        ),
        (
            {
                'type': 'Authentication:success',
                'user': {
                    'crosswalk': {
                        'fhir_id_v2': DEFAULT_SAMPLE_FHIR_ID_V2,
                        'fhir_id_v3': DEFAULT_SAMPLE_FHIR_ID_V3,
                    }
                },
            },
            DEFAULT_SAMPLE_FHIR_ID_V2,
            DEFAULT_SAMPLE_FHIR_ID_V3,
        ),
        (
            {
                'type': 'Authentication:success',
                'user': {
                    'crosswalk': {
                        'fhir_id_v2': None,
                        'fhir_id_v3': None,
                    }
                },
            },
            None,
            None,
        ),
        (
            {
                'type': 'Authentication:success',
                'user': {
                    'crosswalk': {
                        'fhir_id_v2': DEFAULT_SAMPLE_FHIR_ID_V2,
                        'fhir_id_v3': None,
                    }
                },
            },
            DEFAULT_SAMPLE_FHIR_ID_V2,
            None,
        ),
        (
            {
                'type': 'Authentication:success',
                'user': {
                    'crosswalk': {
                        'fhir_id_v2': None,
                        'fhir_id_v3': DEFAULT_SAMPLE_FHIR_ID_V3,
                    }
                },
            },
            None,
            DEFAULT_SAMPLE_FHIR_ID_V3,
        ),
        (
            {
                'type': 'AccessToken',
                'crosswalk': {
                    'fhir_id': DEFAULT_SAMPLE_FHIR_ID_V2,
                },
            },
            DEFAULT_SAMPLE_FHIR_ID_V2,
            None,
        ),
    ],
)
def test_format_log_message_fhir_id_retrieval(log_message, expected_fhir_id_v2, expected_fhir_id_v3):
    """_summary_

    Args:
        log_message: Log message being passed for formatting
        expected_fhir_id_v2: Expected fhir_id_v2 from _format_log_message
        expected_fhir_id_v3: Expected fhir_id_v3 from _format_log_message
    """
    result = log_handler._format_log_message(log_message)
    assert result['fhir_id_v2'] == expected_fhir_id_v2
    if log_message.get('type') != 'AccessToken':
        assert result['fhir_id_v3'] == expected_fhir_id_v3


@pytest.mark.parametrize(
    'log_message, expected_auth_path, expected_grant_type, expected_app_id, expected_app_name, expected_allow',
    [
        (
            {
                'location': '/v2/authorize?foo=bar',
                'req_grant_type': 'authorization_code',
                'auth_app_id': 1,
                'auth_app_name': 'TestApp',
                'allow': False,
            },
            '/v2/authorize',
            'authorization_code',
            1,
            'TestApp',
            'False',
        ),
        (
            {
                'location': '/v2/authorize?foo=bar',
                'req_grant_type': 'authorization_code',
                'resp_app_id': 1,
                'resp_app_name': 'TestApp',
                'allow': True,
            },
            '/v2/authorize',
            'authorization_code',
            1,
            'TestApp',
            'True',
        ),
        (
            {
                'location': '/v2/authorize?foo=bar',
                'req_grant_type': 'authorization_code',
                'req_app_id': 1,
                'req_app_name': 'TestApp',
                'allow': True,
            },
            '/v2/authorize',
            'authorization_code',
            1,
            'TestApp',
            'True',
        ),
    ],
)
def test_format_log_message_other_fields(
    log_message,
    expected_auth_path,
    expected_grant_type,
    expected_app_id,
    expected_app_name,
    expected_allow,
):
    """_summary_

    Args:
        log_message: Log message being passed for formatting
        expected_auth_path: Expected auth_path from _format_log_message
        expected_grant_type: Expected auth_path from _format_log_message
        expected_app_id: Expected auth_path from _format_log_message
        expected_app_name: Expected auth_path from _format_log_message
        expected_allow: Expected auth_path from _format_log_message
    """

    result = log_handler._format_log_message(log_message)
    assert result.get('auth_path') == expected_auth_path
    assert result.get('auth_grant_type') == expected_grant_type
    assert result.get('app_id') == expected_app_id
    assert result.get('app_name') == expected_app_name
    assert result.get('allow') == expected_allow


@pytest.mark.parametrize(
    'log_message, expected_payload, log_message_name',
    [
        (
            {
                'access_token_id': 1612,
                'access_token_scopes': 'profile patient/Patient.rs patient/ExplanationOfBenefit.rs patient/Coverage.rs',
                'app_id': 35,
                'app_name': 'local logging',
                'app_require_demographic_scopes': True,
                'dev_id': 1,
                'dev_name': 'root',
                'elapsed': 0.38216400146484375,
                'end_time': 1790624896.192774,
                'fhir_attribute_count': 7,
                'fhir_bundle_type': 'searchset',
                'fhir_entry_count': 10,
                'fhir_id_v2': DEFAULT_SAMPLE_FHIR_ID_V2,
                'fhir_id_v3': DEFAULT_SAMPLE_FHIR_ID_V3,
                'fhir_resource_id': '876b8bf6-e2bc-4207-aa22-51f396fdf68e',
                'fhir_resource_type': 'Bundle',
                'ip_addr': '192.168.127.1',
                'location': '',
                'path': '/v3/fhir/ExplanationOfBenefit',
                'req_fhir_id_v2': DEFAULT_SAMPLE_FHIR_ID_V2,
                'req_fhir_id_v3': DEFAULT_SAMPLE_FHIR_ID_V3,
                'req_header_accept_encoding': 'gzip, deflate, br',
                'req_header_host': 'localhost:8000',
                'req_header_user_agent': 'PostmanRuntime/2.8.0',
                'req_user_id': 93,
                'req_user_username': 'BBUser00000',
                'request_method': 'GET',
                'request_scheme': 'http',
                'request_uuid': '8be9972e-bb75-11f1-8bfe-02db1dcb95d4',
                'response_code': 200,
                'size': 723995,
                'start_time': 1790624895.810615,
                'type': 'request_response_middleware',
                'user': 'BBUser00000',
                'user_id': 93,
                'user_username': 'BBUser00000',
            },
            {
                'tags': [],
                'value': '{"app_id": 35, "app_name": "local logging", "fhir_id_v2": "-20140000008325", "fhir_id_v3": "-30250000008325", "path": "/v3/fhir/ExplanationOfBenefit", "request_method": "GET", "response_code": 200, "type": "request_response_middleware"}',
                'type': 'text',
            },
            AUDIT_HHS_AUTH_SERVER_REQ_LOGGER,
        ),
        (
            {
                'auth_app_data_access_type': 'THIRTEEN_MONTH',
                'auth_app_id': '35',
                'auth_app_name': 'local logging',
                'auth_client_id': 'iMJqiB3CFRfcQrqxew9uruvV8NjDVN8Wne0jwGYf',  # betterleaks:allow
                'auth_crosswalk_action': 'R',
                'auth_pkce_method': 'S256',
                'auth_require_demographic_scopes': 'True',
                'path': 'v3/mymedicare/sls-callback',
                'request_uuid': '706a138e-bb75-11f1-8bfe-02db1dcb95d4',
                'sub': 'BBUser00000',
                'type': 'Authentication:success',
                'user': {
                    'crosswalk': {
                        'fhir_id_v2': DEFAULT_SAMPLE_FHIR_ID_V2,
                        'fhir_id_v3': DEFAULT_SAMPLE_FHIR_ID_V3,
                        'id': 92,
                        'user_hicn_hash': 'f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948',
                        'user_id_type': 'M',
                    },
                    'id': 93,
                    'username': 'BBUser00000',
                },
            },
            {
                'tags': [],
                'value': '{"auth_crosswalk_action": "R", "auth_require_demographic_scopes": "True", "path": "v3/mymedicare/sls-callback", "type": "Authentication:success", "fhir_id_v2": "-20140000008325", "fhir_id_v3": "-30250000008325", "app_id": "35", "app_name": "local logging"}',
                'type': 'text',
            },
            AUDIT_AUTHN_SLS_LOGGER,
        ),
        (
            {
                'access_token': '11b9e6f5f321d236403871724af71183e4a050f0e1f38e36bf5f6da6d28ac5c4',  # betterleaks:allow
                'action': 'revoked',
                'application': {
                    'data_access_type': 'THIRTEEN_MONTH',
                    'id': 35,
                    'name': 'local logging',
                    'user': {'id': 1, 'username': 'root'},
                },
                'crosswalk': {
                    'fhir_id': '-10000010254618',
                    'id': 92,
                    'user_hicn_hash': 'f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948',
                    'user_id_type': 'M',
                },
                'id': 1613,
                'scopes': 'profile patient/Patient.rs patient/ExplanationOfBenefit.rs patient/Coverage.rs',
                'type': 'AccessToken',
                'user': {'id': 93, 'username': 'BBUser00000'},
            },
            {
                'tags': [],
                'value': '{"action": "revoked", "type": "AccessToken", "fhir_id_v2": "-10000010254618", "app_id": 35, "app_name": "local logging"}',
                'type': 'text',
            },
            AUDIT_AUTHZ_TOKEN_LOGGER,
        ),
    ],
)
@patch('apps.logging.its_log_handler.ITSLogAPIHandler._post_to_api')
def test_post_api_is_called_with_specific_payload(mock_post_to_api, log_message, expected_payload, log_message_name):
    with patch.dict(os.environ, {'ITS_LOG_API_ENABLED': 'True'}):
        record = logging.makeLogRecord(
            {
                'name': log_message_name,
                'level': logging.INFO,
                'msg': json.dumps(log_message),
            }
        )
        log_handler.emit(record)
        mock_post_to_api.assert_called_with(expected_payload)
