import json
import logging
import threading
from typing import Any, Dict

import requests

TYPES_TO_SKIP = ['fhir_post_fetch', 'fhir_pre_fetch', 'fhir_auth_post_fetch']
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
    # API_KEY = "12345678901234561234567890123456"
    API_KEY = '1234567890123456123456789012345612345678901234561234567890123456'

    def emit(self, record):
        print('record check: ', record)
        log_message = self.parse_log_message(record.__dict__)
        if log_message.get('type') in TYPES_TO_SKIP or 'testclient' in log_message.get('path', ''):
            return

        updated_log_message = self._format_log_message(log_message)
        if not updated_log_message:
            return
        payload = self._build_payload(updated_log_message)
        print('payload: ', payload)

        threading.Thread(target=self._post_to_api, args=(payload,), daemon=True).start()

    def parse_log_message(self, record):
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
        tags = []
        print('LOG MESSAGE: ', log_message)
        filtered_log = {k: v for k, v in log_message.items() if k in ACCEPTED_LOG_KEYS}

        print('filtered_log: ', filtered_log)

        return {
            'tags': tags,
            'value': json.dumps(filtered_log),
            'type': 'text',
        }

    def _build_payload_cluster_events(self, key, value, application_id) -> Dict[str, Any]:

        formatted_tag = [key]
        if application_id:
            formatted_tag.append(application_id)

        return {'tags': formatted_tag, 'value': str(value), 'type': 'text'}

    def _format_log_message(self, log_message: Dict[str, Any]) -> Dict[str, Any]:
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
        if not log_message.get('app_id') and log_message.get('application'):
            log_message['app_id'] = log_message['application'].get('id')
            log_message['app_name'] = log_message['application'].get('name')

        if log_message.get('allow'):
            if log_message.get('allow') is True:
                log_message['allow'] = 'True'
            else:
                log_message['allow'] = 'False'

        return log_message

    def _post_to_api(self, payload):
        try:
            response = requests.post(self.API_URL, headers={'x-api-key': self.API_KEY}, json=payload, timeout=2)
            return response
        except Exception:
            # Do not let ITS-log failures crash BlueButton
            pass
