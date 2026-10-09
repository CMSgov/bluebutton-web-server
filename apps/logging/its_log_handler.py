import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

import requests

from apps.logging.constants import HHS_SERVER_LOGNAME_FMT

logger = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))

TYPES_TO_SKIP = [
    'fhir_post_fetch',
    'fhir_pre_fetch',
    'fhir_auth_post_fetch',
    'global_state_metrics',
    'global_state_metrics_per_app',
]
# Other possibilities:
# auth_app_data_access_type, auth_app_id, path, req_grant_Type,
ACCEPTED_LOG_KEYS = [
    'app_name',
    'app_id',
    'type',
    'response_code',
    'fhir_id_v2',
    'fhir_id_v3',
    'allow',
    'auth_status',
    'req_grant_type',
    'auth_require_demographic_scopes',
    'share_demographic_scopes',
    'path',
    'request_method',
    'auth_grant_type',
    'action',
    'sls_userinfo_status_code',
    'auth_crosswalk_action',
    'crosswalk_fhir_id',
    'auth_path',
    'patient_match_found',
    'csp',
    'patient',
    'req_qparam_lastupdated',
    'req_qparam__source',
    'req_qparam__tag',
    'auth_share_samhsa_data',
    # 'auth_app_id',
    # 'auth_app_name',
]
GRAB_FHIR_ID_FROM_USER_CROSSWALK = ['Authentication:success', 'Authorization']
GRAB_FHIR_ID_FROM_CROSSWALK = ['AccessToken']


class ITSLogAPIHandler(logging.Handler):
    """
    Custom logging handler that forwards log records to the ITS Log API.
    Fires asynchronously so it never blocks the main thread.
    """

    API_URL = 'http://host.docker.internal:8888/v1/log/create'
    API_KEY = '1234567890123456123456789012345612345678901234561234567890123456'
    executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix='its-log')

    def emit(self, record) -> None:
        """Format the log message if it is a log type we want to post to its-log,
        then send the log event to its-log. There is no check on a env var or waffle switch
        here as the ITS_LOG_API_ENABLED env var controls in base_local.py and base_ec2.py determines
        if we ever hit this function.

        Args:
            record: Log record being checked and formatted for posting to its-log
        """
        log_message = self._parse_log_message(record.__dict__)
        if (
            log_message.get('type') in TYPES_TO_SKIP
            or 'testclient' in log_message.get('path', '')
            or 'admin' in log_message.get('path', '')
        ):
            return

        updated_log_message = self._format_log_message(log_message)
        if not updated_log_message:
            return
        payload = self._build_payload(updated_log_message)

        self.executor.submit(self._post_to_api, payload)

    def _parse_log_message(self, record) -> Dict[str, Any]:
        """Extracts the msg attribute of the log record, checks that value is a string that starts with
        { or [, and returns the dictionary typed value of the msg attribute

        Args:
            record: Log record being checked and formatted for posting to its-log

        Returns:
            Dict[str, Any]: The dictionary typed vale of the log record's msg attribute
        """
        msg = record.get('msg', '')

        # Only attempt JSON parsing if it looks like a JSON object or array
        if isinstance(msg, str) and msg.strip().startswith(('{', '[')):
            try:
                return json.loads(msg)
            except (json.JSONDecodeError, ValueError):
                pass

        # Return None (or the raw string) if it's not valid JSON
        return {}

    def _build_payload(self, log_message) -> Dict[str, Any]:
        """Builds a paylod for the its-log API events endpoint. Tags is currently just an empty
        list, could be removed or modified in the future. We only want certain log attributes in
        the value column of itslog_events, so we filter for the specific log attributes that we want.

        Args:
            log_message (dict): Dictionary containing the details of the log event

        Returns:
            Dict[str, Any]: Formatted payload that the its-log API event endpoint expects
        """
        tags = []
        filtered_log = {k: v for k, v in log_message.items() if k in ACCEPTED_LOG_KEYS}

        return {
            'tags': tags,
            'value': json.dumps(filtered_log),
            'type': 'text',
        }

    def _format_log_message(self, log_message: Dict[str, Any]) -> Dict[str, Any]:
        """Format the log_message before building the its-log API payload, so the payload
        sent to its-log will have the fields that the different ETL steps are looking for
        to calculate metrics

        Args:
            log_message (Dict[str, Any]): Dictionary containing the details of the log event

        Returns:
            Dict[str, Any]: Formatted log message with specific keys that are looked for in our data pipeline
        """
        if log_message.get('type'):
            if log_message.get('type') in GRAB_FHIR_ID_FROM_USER_CROSSWALK:
                log_message['fhir_id_v2'] = log_message.get('user').get('crosswalk').get('fhir_id_v2')
                log_message['fhir_id_v3'] = log_message.get('user').get('crosswalk').get('fhir_id_v3')
            elif log_message.get('type') in GRAB_FHIR_ID_FROM_CROSSWALK:
                log_message['fhir_id_v2'] = log_message.get('crosswalk').get('fhir_id')
        if log_message.get('code'):
            log_message['response_code'] = log_message.get('code')
        if (
            '?' in log_message.get('location', '')
            and 'authorize' in log_message.get('location', '')
            and log_message.get('location', '').startswith('/v')
        ):
            log_message['auth_path'] = log_message.get('location').split('?')[0]

        if log_message.get('req_grant_type'):
            log_message['auth_grant_type'] = log_message.get('req_grant_type')

        if not log_message.get('app_id') and log_message.get('auth_app_id'):
            log_message['app_id'] = log_message.get('auth_app_id')
        if not log_message.get('app_name') and log_message.get('auth_app_name'):
            log_message['app_name'] = log_message.get('auth_app_name')
        if not log_message.get('app_id') and log_message.get('resp_app_id'):
            log_message['app_id'] = log_message.get('resp_app_id')
        if not log_message.get('app_name') and log_message.get('resp_app_name'):
            log_message['app_name'] = log_message.get('resp_app_name')
        if not log_message.get('app_id') and log_message.get('req_app_id'):
            log_message['app_id'] = log_message.get('req_app_id')
        if not log_message.get('app_name') and log_message.get('req_app_name'):
            log_message['app_name'] = log_message.get('req_app_name')
        if not log_message.get('app_id') and log_message.get('application'):
            log_message['app_id'] = log_message['application'].get('id')
            log_message['app_name'] = log_message['application'].get('name')

        if 'allow' in log_message:
            log_message['allow'] = 'True' if log_message.get('allow') is True else 'False'

        return log_message

    def _post_to_api(self, payload) -> None:
        """Post the given payload to the its-log API events endpoint

        Args:
            payload (dict): The payload being posted to the its-log API
        """
        logger.info(f'Payload for its-log: {json.dumps(payload)}')
        try:
            requests.post(self.API_URL, headers={'x-api-key': self.API_KEY}, json=payload, timeout=5)
            logger.info('Successfully posted to its-log')
        except Exception:
            # Do not let ITS-log failures crash BlueButton
            logger.error('Failed to post to its-log API')
