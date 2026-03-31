import logging
import json
import threading
from typing import Any, Dict
import requests

TYPES_TO_SKIP = ['slsx_token', 'slsx_userinfo', '']
# Other possibilities:
# auth_app_data_access_type, auth_app_id, path, req_grant_Type,
ACCEPTED_LOG_KEYS = ['app_name', 'app_id', 'type', 'response_code', 'fhir_id_v2', 'fhir_id_v3']
GRAB_FHIR_ID_FROM_USER_CROSSWALK = ['Authentication:success', 'Authorization']
GRAB_FHIR_ID_FROM_CROSSWALK = ['AccessToken']


class ITSLogAPIHandler(logging.Handler):
    """
    Custom logging handler that forwards log records to the ITS Log API.
    Fires asynchronously so it never blocks the main thread.
    """

    API_URL = "http://host.docker.internal:8888/v1/log"
    API_KEY = "12345678901234561234567890123456"
    # API_KEY = "1234567890123456123456789012345612345678901234561234567890123456"

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
        payload = self._build_payload(log_message, record)
        print("PAYLOAD CHECK: ", payload)

        # Fire in a background thread — never block the caller
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

    def _build_payload(self, log_message, record) -> Dict[str, Any]:
        tags = []
        print("LOG MESSAGE: ", log_message)

        if log_message.get('auth_app_id'):
            tags.append(log_message.get('auth_app_id'))
        if log_message.get('type'):
            tags.append(log_message.get('type'))
            if log_message.get('type') in GRAB_FHIR_ID_FROM_USER_CROSSWALK:
                print("what was the type: ", log_message.get('type'))
                log_message['fhir_id_v2'] = log_message.get('user').get('crosswalk').get('fhir_id_v2')
                log_message['fhir_id_v3'] = log_message.get('user').get('crosswalk').get('fhir_id_v3')
            elif log_message.get('type') in GRAB_FHIR_ID_FROM_CROSSWALK:
                log_message['fhir_id_v2'] = log_message.get('crosswalk').get('fhir_id')

        # Logger name (e.g. "apps.dot_ext.views.fhir")
        # tags.append(record.name)

        # Extra fields passed via extra={} in the log call
        app_id = getattr(record, 'application_id', None)
        if app_id:
            tags.append(str(app_id))

        print("tag check: ", tags)

        log_message_list = [f"{k}:{v}" for k, v in log_message.items() if k in ACCEPTED_LOG_KEYS]
        # log_message_list = [f"{k}:{v}" for k, v in log_message.items()]
        print("log_message_list: ", log_message_list)
        return {
            'tags': tags,
            'value': " ".join(log_message_list),
            # 'value': 'test',
            'type': 'text'
        }

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
