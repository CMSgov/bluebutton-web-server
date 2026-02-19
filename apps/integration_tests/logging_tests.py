import copy
import json
import re

from json.decoder import JSONDecodeError

from apps.integration_tests.common_utils import validate_json_schema
from apps.integration_tests.selenium_tests import TestBlueButtonAPI
from apps.integration_tests.constants import (
    EXPECTED_LOGGING_EVENTS,
    LOG_FILE,
    MIDDLEWARE_LOG_EVENT_TYPE,
)


class TestLoggings(TestBlueButtonAPI):
    '''
    Test loggings generated from authorization and fhir flow using the built in testclient as
    the driver (selenium)
    '''
    def _validate_events(self):
        with open(LOG_FILE, 'r') as f:
            log_records = f.readlines()
            start_validation = False
            expected_events = copy.deepcopy(EXPECTED_LOGGING_EVENTS)
            while log_records:
                r = log_records.pop(0)
                try:
                    event_json = json.loads(r)
                    e_type = event_json.get('type', 'NO TYPE INFO')
                    e_user_agent = event_json.get('req_header_user_agent')
                    if e_user_agent is not None and not e_user_agent.startswith("curl") and e_type == MIDDLEWARE_LOG_EVENT_TYPE:
                        p = event_json.get('path', None)
                        if not start_validation:
                            if p == "/":
                                start_validation = True
                        else:
                            event_desc = expected_events.pop(0)
                            print("EVENT_DESC={}".format(event_desc))
                            print("PATH={}".format(p))
                            if event_desc.get('path_regex') is not None:
                                assert re.match(event_desc.get('path_regex'), p)
                            else:
                                assert p == event_desc.get('path')
                            assert (validate_json_schema(event_desc.get('schema'), event_json))
                except JSONDecodeError:
                    # skip non json line
                    pass

            # all log events present and validated
            assert len(expected_events) == 0

    def test_auth_fhir_flows_logging(self):
        self.test_auth_grant_fhir_calls_v2()
        print("validating logging events in log...")
        self._validate_events()
