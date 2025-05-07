import copy
import json
import re

from json.decoder import JSONDecodeError

from .common_utils import validate_json_schema
from .selenium_tests import TestBlueButtonAPI
from .log_event_schemas import (
    LOG_MIDDLEWARE_FHIR_READ_EVENT_SCHEMA,
    LOG_MIDDLEWARE_FHIR_SEARCH_EVENT_SCHEMA,
    LOG_MIDDLEWARE_FHIR_NAVIGATION_EVENT_SCHEMA,
    LOG_MIDDLEWARE_FHIR_USERINFO_EVENT_SCHEMA,
    LOG_MIDDLEWARE_POST_TOKEN_EVENT_SCHEMA,
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

LOG_FILE = "./docker-compose/tmp/bb2_logging_sink.log"
MIDDLEWARE_LOG_EVENT_TYPE = "request_response_middleware"

EXPECTED_LOGGING_EVENTS = [
    {
        # clicked test client
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/testclient/",
    },
    {
        # auth link
        "schema": LOG_MIDDLEWARE_TESTCLIENT_AUTHLINK_EVENT_SCHEMA,
        "path": "/testclient/authorize-link-v2",
    },
    {
        # authorize as a bene
        "schema": LOG_MIDDLEWARE_AUTH_START_EVENT_SCHEMA,
        "path_regex": "/v[12]/o/authorize/"
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
        "path_regex": "/v[12]/o/authorize/.+/"
    },
    {
        "schema": LOG_MIDDLEWARE_ACCESS_GRANT_EVENT_SCHEMA,
        "path_regex": "/v[12]/o/authorize/.+/"
    },
    {
        "schema": LOG_MIDDLEWARE_POST_TOKEN_EVENT_SCHEMA,
        "path": "/v2/o/token/",
    },
    {
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/v2/connect/userinfo",
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
        "path_regex": "/v2/fhir/Patient/-20140000008325|/v2/fhir/Patient/-19990000000001"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_READ_EVENT_SCHEMA,
        "path": "/testclient/PatientV2"
    },
    {
        # first Coverage
        "schema": LOG_MIDDLEWARE_FHIR_SEARCH_EVENT_SCHEMA,
        "path": "/v2/fhir/Coverage/"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_SEARCH_EVENT_SCHEMA,
        "path": "/testclient/CoverageV2"
    },
    {
        # last Coverage
        "schema": LOG_MIDDLEWARE_FHIR_NAVIGATION_EVENT_SCHEMA,
        "path": "/v2/fhir/Coverage/"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_NAVIGATION_EVENT_SCHEMA,
        "path": "/testclient/CoverageV2"
    },
    {
        # test client fhir links page
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/testclient/"
    },
    {
        # first EOB
        "schema": LOG_MIDDLEWARE_FHIR_SEARCH_EVENT_SCHEMA,
        "path": "/v2/fhir/ExplanationOfBenefit/"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_SEARCH_EVENT_SCHEMA,
        "path": "/testclient/ExplanationOfBenefitV2"
    },
    {
        # last EOB
        "schema": LOG_MIDDLEWARE_FHIR_NAVIGATION_EVENT_SCHEMA,
        "path": "/v2/fhir/ExplanationOfBenefit/"
    },
    {
        "schema": LOG_MIDDLEWARE_TESTCLIENT_FHIR_NAVIGATION_EVENT_SCHEMA,
        "path": "/testclient/ExplanationOfBenefitV2"
    },
    {
        # test client fhir links page
        "schema": LOG_MIDDLEWARE_EVENT_SCHEMA,
        "path": "/testclient/"
    },
    {
        # userinfo ep
        "schema": LOG_MIDDLEWARE_FHIR_USERINFO_EVENT_SCHEMA,
        "path": "/v2/connect/userinfo"
    },
    {
        # userinfo testclient url
        "schema": LOG_MIDDLEWARE_TESTCLIENT_MISCINFO_EVENT_SCHEMA,
        "path": "/testclient/userinfoV2"
    },
    {
        # meta data
        "schema": LOG_MIDDLEWARE_TESTCLIENT_MISCINFO_EVENT_SCHEMA,
        "path": "/testclient/metadataV2"
    },
    {
        # openid discovery
        "schema": LOG_MIDDLEWARE_TESTCLIENT_MISCINFO_EVENT_SCHEMA,
        "path": "/testclient/openidConfigV2"
    },
    {
        # restart test client - go to test client home page with v1, v2 get sample token buttons
        "schema": LOG_MIDDLEWARE_TESTCLIENT_MISCINFO_EVENT_SCHEMA,
        "path": "/testclient/restart"
    },

]


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
        self.test_auth_grant_pkce_fhir_calls_v2()
        print("validating logging events in log...")
        self._validate_events()
