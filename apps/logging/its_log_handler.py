import logging
import json
import threading
from typing import Any, Dict
import requests
import uuid

TYPES_TO_SKIP = ['slsx_token', 'slsx_userinfo']
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
    'auth_path'
]
GRAB_FHIR_ID_FROM_USER_CROSSWALK = ['Authentication:success', 'Authorization']
GRAB_FHIR_ID_FROM_CROSSWALK = ['AccessToken']


class ITSLogAPIHandler(logging.Handler):
    """
    Custom logging handler that forwards log records to the ITS Log API.
    Fires asynchronously so it never blocks the main thread.
    """

    API_URL = "http://host.docker.internal:8888/v1/log/create"
    # API_KEY = "12345678901234561234567890123456"
    API_KEY = "1234567890123456123456789012345612345678901234561234567890123456"

    def emit(self, record):
        print("RECORD CHECK INITIAL: ", record.__dict__)

        log_message = self.parse_log_message(record.__dict__)
        print("type check big dog: ", log_message.get('type'))
        # if (
        #     log_message.get('type') not in GRAB_FHIR_ID_FROM_USER_CROSSWALK
        #     and log_message.get('type') not in GRAB_FHIR_ID_FROM_CROSSWALK
        # ):
        #     print("not a log type to post to ITS-log")
        #     return
        cluster_uuid = str(uuid.uuid4())
        updated_log_message = self._format_log_message(log_message)
        app_id = getattr(record, 'application_id', None)
        print("app_id: ", app_id)

        for key, value in updated_log_message.items():
            print("key/val in loop: ", key, value)
            if key in ACCEPTED_LOG_KEYS:
                payload = self._build_payload(key, value, app_id)
                payload['cluster'] = cluster_uuid
                print("payload: ", payload)
                threading.Thread(
                    target=self._post_to_api,
                    args=(payload,),
                    daemon=True
                ).start()

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

    def _build_payload(self, key, value, application_id) -> Dict[str, Any]:
        formatted_tag = [key]
        if application_id:
            formatted_tag.append(application_id)

        return {
            'tags': formatted_tag,
            'value': str(value),
            'type': 'text'
        }

    def _format_log_message(self, log_message: Dict[str, Any]) -> Dict[str, Any]:
        if log_message.get('type'):
            if log_message.get('type') in GRAB_FHIR_ID_FROM_USER_CROSSWALK:
                print("what was the type: ", log_message.get('type'))
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

        return log_message

    def _post_to_api(self, payload):
        print("WHAT ARE WE POSTING: ", payload)
        try:
            response = requests.post(
                self.API_URL,
                headers={'x-api-key': self.API_KEY},
                json=payload,
                timeout=2
            )
            print("WHAT IS THE RESPONSE: ", response.text)
            return response
        except Exception as e:
            print("ERROR FROM ITS-LOG handler 1217: ", e)
            # Do not let ITS-log failures crash BlueButton
            pass
