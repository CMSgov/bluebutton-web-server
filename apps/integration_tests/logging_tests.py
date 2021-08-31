import copy
import json
import re
import logging

from json.decoder import JSONDecodeError

from apps.integration_tests.common_utils import validate_json_schema
from apps.integration_tests.selenium_tests import SeleniumTests
from apps.integration_tests.log_event_schemas import (
    LOG_MIDDLEWARE_FHIR_READ_EVENT_SCHEMA,
    LOG_MIDDLEWARE_FHIR_SEARCH_EVENT_SCHEMA,
    LOG_MIDDLEWARE_FHIR_NAVIGATION_EVENT_SCHEMA,
    LOG_MIDDLEWARE_FHIR_USERINFO_EVENT_SCHEMA,
    LOG_MIDDLEWARE_POST_EVENT_SCHEMA,
    LOG_MIDDLEWARE_TESTCLIENT_FHIR_NAVIGATION_EVENT_SCHEMA,
    LOG_MIDDLEWARE_TESTCLIENT_FHIR_READ_EVENT_SCHEMA,
    LOG_MIDDLEWARE_TESTCLIENT_FHIR_SEARCH_EVENT_SCHEMA,
    LOG_MIDDLEWARE_ACCESS_GRANT_EVENT_SCHEMA,
    LOG_MIDDLEWARE_AUTHORIZE_EVENT_SCHEMA,
    LOG_MIDDLEWARE_EVENT_SCHEMA,
    LOG_MIDDLEWARE_MEDICARE_CALLBACK_EVENT_SCHEMA,
    LOG_MIDDLEWARE_MEDICARE_LOGIN_EVENT_SCHEMA,
    LOG_MIDDLEWARE_TESTCLIENT_AUTHLINK_EVENT_SCHEMA,
    LOG_MIDDLEWARE_AUTH_START_EVENT_SCHEMA,
    LOG_MIDDLEWARE_TESTCLIENT_MISCINFO_EVENT_SCHEMA
)

TEST_LOGGING_FILE = "./docker-compose/tmp/bb2_logging_test.log"
MIDDLEWARE_LOG_EVENT_TYPE = "request_response_middleware"

EXPECTED_LOGGING_EVENTS = [
    {
        # clicked test client
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/testclient/",
    },
    {
        # v1 auth link
        "schema": LOG_MIDDLEWARE_TESTCLIENT_AUTHLINK_EVENT_SCHEMA,
        "path": "/testclient/authorize-link",
    },
    {
        # authorize as a bene
        "schema": LOG_MIDDLEWARE_AUTH_START_EVENT_SCHEMA,
        "path": "/v1/o/authorize/",
    },
    {
        "schema": LOG_MIDDLEWARE_MEDICARE_LOGIN_EVENT_SCHEMA,
        "path": "/mymedicare/login"
    },
    {
        "schema": LOG_MIDDLEWARE_MEDICARE_CALLBACK_EVENT_SCHEMA,
        "path": "/mymedicare/sls-callback",
    },
    {
        "schema": LOG_MIDDLEWARE_AUTHORIZE_EVENT_SCHEMA,
        "path_regex": "/v1/o/authorize/.+/"
    },
    {
        "schema": LOG_MIDDLEWARE_ACCESS_GRANT_EVENT_SCHEMA,
        "path_regex": "/v1/o/authorize/.+/"
    },
    {
        "schema": LOG_MIDDLEWARE_POST_EVENT_SCHEMA,
        "path": "/v1/o/token/",
    },
    {
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/v1/connect/userinfo",
    },
    {
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/testclient/callback",
        # "response_code": 301
    },
    {
        # redirect to test client fhir links page
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/testclient/"
    },
    {
        "schema": LOG_MIDDLEWARE_FHIR_READ_EVENT_SCHEMA,
        "path": "/v1/fhir/Patient/-20140000008325"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_READ_EVENT_SCHEMA,
        "path": "/testclient/Patient"
    },
    {
        # first Coverage
        "schema": LOG_MIDDLEWARE_FHIR_SEARCH_EVENT_SCHEMA,
        "path": "/v1/fhir/Coverage/"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_SEARCH_EVENT_SCHEMA,
        "path": "/testclient/Coverage"
    },
    {
        # last Coverage
        "schema": LOG_MIDDLEWARE_FHIR_NAVIGATION_EVENT_SCHEMA,
        "path": "/v1/fhir/Coverage/"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_NAVIGATION_EVENT_SCHEMA,
        "path": "/testclient/Coverage"
    },
    {
        # test client fhir links page
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/testclient/"
    },
    {
        # first EOB
        "schema": LOG_MIDDLEWARE_FHIR_SEARCH_EVENT_SCHEMA,
        "path": "/v1/fhir/ExplanationOfBenefit/"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_SEARCH_EVENT_SCHEMA,
        "path": "/testclient/ExplanationOfBenefit"
    },
    {
        # last EOB
        "schema": LOG_MIDDLEWARE_FHIR_NAVIGATION_EVENT_SCHEMA,
        "path": "/v1/fhir/ExplanationOfBenefit/"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_NAVIGATION_EVENT_SCHEMA,
        "path": "/testclient/ExplanationOfBenefit"
    },
    {
        # test client fhir links page
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/testclient/"
    },
    {
        # userinfo ep
        "schema": LOG_MIDDLEWARE_FHIR_USERINFO_EVENT_SCHEMA,
        "path": "/v1/connect/userinfo"
    },
    {
        # userinfo testclient url
        "schema": LOG_MIDDLEWARE_TESTCLIENT_MISCINFO_EVENT_SCHEMA,
        "path": "/testclient/userinfo"
    },
    {
        # meta data
        "schema": LOG_MIDDLEWARE_TESTCLIENT_MISCINFO_EVENT_SCHEMA,
        "path": "/testclient/metadata"
    },
    {
        # openid discovery
        "schema": LOG_MIDDLEWARE_TESTCLIENT_MISCINFO_EVENT_SCHEMA,
        "path": "/testclient/openidConfig"
    },
    {
        # restart test client - go to test client home page with v1, v2 get sample token buttons
        "schema": LOG_MIDDLEWARE_TESTCLIENT_MISCINFO_EVENT_SCHEMA,
        "path": "/testclient/restart"
    },

]


class LoggingTests(SeleniumTests):
    '''
    Test loggings generated from authorization and fhir flow using the built in testclient as
    the driver (selenium)
    '''
    def _validate_events(self):
        # validate middleware logging records in log file ./docker-compose/tmp/bb2_logging_test.log
        with open(TEST_LOGGING_FILE, 'r') as f:
            log_records = f.readlines()
            start_validation = False
            expected_events = copy.deepcopy(EXPECTED_LOGGING_EVENTS)
            while log_records:
                r = log_records.pop(0)
                try:
                    event_json = json.loads(r)
                    if event_json.get('type', 'NO TYPE INFO') == MIDDLEWARE_LOG_EVENT_TYPE:
                        p = event_json.get('path', None)
                        if not start_validation:
                            if p == "/":
                                start_validation = True
                        else:
                            event_desc = expected_events.pop(0)
                            if event_desc.get('path_regex') is not None:
                                self.assertTrue(re.match(event_desc.get('path_regex'), p))
                            else:
                                self.assertEqual(p, event_desc.get('path'))
                            self.assertTrue(validate_json_schema(event_desc.get('schema'), event_json))
                except JSONDecodeError:
                    # skip non json line
                    pass

            # all log events present and validated
            self.assertEqual(len(expected_events), 0)

    def test_auth_fhir_flows_logging(self):
        # direct relevant log records to the file
        audit_logger = logging.getLogger("audit")
        file_handler = logging.FileHandler(TEST_LOGGING_FILE)
        for h in audit_logger.handlers[:]:
            audit_logger.removeHandler(h)
        audit_logger.addHandler(file_handler)
        audit_logger.setLevel(logging.INFO)
        self.test_auth_grant_fhir_calls_v1()
        print("validating logging events in log...")
        self._validate_events()
