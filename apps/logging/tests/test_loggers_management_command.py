import copy
import json
import jsonschema

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test.client import Client
from jsonschema import validate
from io import StringIO
from oauth2_provider.models import get_access_token_model, get_application_model

from apps.dot_ext.utils import (
    remove_application_user_pair_tokens_data_access,
)
import apps.logging.request_logger as logging
from apps.test import BaseApiTest

from .audit_logger_schemas import (
    GLOBAL_STATE_METRICS_LOG_SCHEMA,
    GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA,
)

AccessToken = get_access_token_model()
Application = get_application_model()
User = get_user_model()

# Create copies of schemas for testing
TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA = copy.deepcopy(GLOBAL_STATE_METRICS_LOG_SCHEMA)
TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA = copy.deepcopy(
    GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA
)


class TestLoggersGlobalMetricsManagementCommand(BaseApiTest):
    def setUp(self):
        # Setup the RequestFactory
        self.client = Client()
        self._redirect_loggers()

    def tearDown(self):
        self._cleanup_logger()

    def _get_log_content(self, logger_name):
        return self._collect_logs().get(logger_name)

    def _validateJsonSchema(self, schema, content):
        try:
            validate(instance=content, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            # Show error info for debugging
            print("jsonschema.exceptions.ValidationError: ", e)
            return False
        return True

    def _validate_global_state_metrics_log(self, validate_dict):
        """
        Validate log line has expected values.
        """
        # Get all log entries
        log_content = self._get_log_content(logging.AUDIT_GLOBAL_STATE_METRICS_LOGGER)
        self.assertIsNotNone(log_content)

        # Set buffer to read log line from log_content
        log_content_buf = StringIO(log_content)

        # Get last global_state_metrics log entry
        for line in log_content_buf:
            line_dict = json.loads(line)
            if line_dict["type"] == "global_state_metrics":
                log_dict = line_dict

        # Update Json Schema for assert
        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"]["real_bene_cnt"]["enum"] = [
            validate_dict["real_bene_cnt"]
        ]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"]["synth_bene_cnt"]["enum"] = [
            validate_dict["synth_bene_cnt"]
        ]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"]["real_bene_grant_cnt"][
            "enum"
        ] = [validate_dict["real_bene_grant_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"]["synth_bene_grant_cnt"][
            "enum"
        ] = [validate_dict["synth_bene_grant_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"]["real_bene_token_distinct_cnt"][
            "enum"
        ] = [validate_dict["real_bene_token_distinct_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"]["synth_bene_token_distinct_cnt"][
            "enum"
        ] = [validate_dict["synth_bene_token_distinct_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"][
            "real_bene_grant_distinct_cnt"
        ]["enum"] = [validate_dict["real_bene_grant_distinct_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"][
            "synth_bene_grant_distinct_cnt"
        ]["enum"] = [validate_dict["synth_bene_grant_distinct_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"][
            "real_bene_grant_arch_distinct_cnt"
        ]["enum"] = [validate_dict["real_bene_grant_arch_distinct_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"][
            "synth_bene_grant_arch_distinct_cnt"
        ]["enum"] = [validate_dict["synth_bene_grant_arch_distinct_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"][
            "real_bene_grant_and_arch_union_cnt"
        ]["enum"] = [validate_dict["real_bene_grant_and_arch_union_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"][
            "synth_bene_grant_and_arch_union_cnt"
        ]["enum"] = [validate_dict["synth_bene_grant_and_arch_union_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"]["global_apps_active_cnt"][
            "enum"
        ] = [validate_dict["global_apps_active_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"]["global_apps_inactive_cnt"][
            "enum"
        ] = [validate_dict["global_apps_inactive_cnt"]]

        TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"][
            "global_apps_require_demographic_scopes_cnt"
        ]["enum"] = [validate_dict["global_apps_require_demographic_scopes_cnt"]]

        # Validate with test schema copy.
        self.assertTrue(
            self._validateJsonSchema(TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA, log_dict)
        )

        # Validate with original schema copy.
        self.assertTrue(
            self._validateJsonSchema(GLOBAL_STATE_METRICS_LOG_SCHEMA, log_dict)
        )

    def _validate_global_state_per_app_metrics_log(self, validate_apps_dict):

        for app_name in validate_apps_dict:
            # Get all log entries
            log_content = self._get_log_content(
                logging.AUDIT_GLOBAL_STATE_METRICS_LOGGER
            )
            self.assertIsNotNone(log_content)

            # Set buffer to read log line from log_content
            log_content_buf = StringIO(log_content)

            # Get last global_state_per_app_metrics log entry for app_name
            # log_line = {}
            for line in log_content_buf:
                line_dict = json.loads(line)
                if line_dict["type"] == "global_state_metrics_per_app":
                    if line_dict["name"] == app_name:
                        log_dict = line_dict

            print("-----  FOUND FOR APP:  ", log_dict)

            # Update Json Schema
            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"]["name"][
                "pattern"
            ] = app_name

            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"]["active"][
                "enum"
            ] = validate_apps_dict[app_name]["active"]

            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"][
                "require_demographic_scopes"
            ]["enum"] = validate_apps_dict[app_name]["require_demographic_scopes"]

            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"]["real_bene_cnt"][
                "enum"
            ] = [validate_apps_dict[app_name]["real_bene_cnt"]]

            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"][
                "synth_bene_cnt"
            ]["enum"] = [validate_apps_dict[app_name]["synth_bene_cnt"]]

            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"][
                "real_bene_grant_arch_distinct_cnt"
            ]["enum"] = [
                validate_apps_dict[app_name]["real_bene_grant_arch_distinct_cnt"]
            ]

            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"][
                "synth_bene_grant_arch_distinct_cnt"
            ]["enum"] = [
                validate_apps_dict[app_name]["synth_bene_grant_arch_distinct_cnt"]
            ]

            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"][
                "real_bene_grant_and_arch_union_cnt"
            ]["enum"] = [
                validate_apps_dict[app_name]["real_bene_grant_and_arch_union_cnt"]
            ]

            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"][
                "synth_bene_grant_and_arch_union_cnt"
            ]["enum"] = [
                validate_apps_dict[app_name]["synth_bene_grant_and_arch_union_cnt"]
            ]

            # Validate with test schema copy.
            self.assertTrue(
                self._validateJsonSchema(
                    TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA, log_dict
                )
            )

            # Validate with orig schema.
            self.assertTrue(
                self._validateJsonSchema(
                    GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA, log_dict
                )
            )

    def test_management_command_logging(self):
        """
        Setup variety of real/synth users, apps and grants for testing global state metrics logging.
        """

        # This dict is used to validate type == "global_state_metrics_per_app" log events.
        validate_apps_dict = {}

        remove_grant_access_list = []
        """
        TEST #1: Adds the following:
          5x synth benes to app0
          3x real benese to app0
          2x synth benes to app1
          5x real benes to app1
        """
        # Create 5x synth benes -20000000000000 thru -20000000000004 connected to app0
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="-2000000000000", count=5, app_name="app0"
        )

        # Add app & user tuples to remove in TEST #3
        remove_grant_access_list.append((app, user_dict["-20000000000002"]))
        remove_grant_access_list.append((app, user_dict["-20000000000003"]))
        remove_grant_access_list.append((app, user_dict["-20000000000004"]))

        # Create 3x real benes 40000000000000 thru 40000000000002 connected to app0
        self._create_range_users_app_token_grant(
            start_fhir_id="4000000000000", count=3, app_name="app0"
        )

        # Create 2x synth benes -30000000000000 thru -30000000000001 connected to app1
        self._create_range_users_app_token_grant(
            start_fhir_id="-3000000000000", count=2, app_name="app1"
        )

        # Create 5x real benes 50000000000000 thru 50000000000004 connected to app1
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="5000000000000", count=5, app_name="app1"
        )

        # Add app & user tuples to remove in TEST #3
        remove_grant_access_list.append((app, user_dict["50000000000001"]))
        remove_grant_access_list.append((app, user_dict["50000000000003"]))

        call_command("log_global_state_metrics", stdout=StringIO(), stderr=StringIO())

        self._validate_global_state_metrics_log(
            {
                "real_bene_cnt": 8,
                "synth_bene_cnt": 7,
                "real_bene_grant_cnt": 8,
                "synth_bene_grant_cnt": 7,

                "real_bene_token_distinct_cnt": 8,
                "synth_bene_token_distinct_cnt": 7,


                "real_bene_grant_distinct_cnt": 8,
                "synth_bene_grant_distinct_cnt": 7,
                "real_bene_grant_arch_distinct_cnt": 0,
                "synth_bene_grant_arch_distinct_cnt": 0,
                "real_bene_grant_and_arch_union_cnt": 8,
                "synth_bene_grant_and_arch_union_cnt": 7,
                "global_apps_active_cnt": 2,
                "global_apps_inactive_cnt": 0,
                "global_apps_require_demographic_scopes_cnt": 2,
            }
        )

        validate_apps_dict.update(
            {
                "app0": {
                    "active": [True],
                    "require_demographic_scopes": [True],
                    "real_bene_cnt": 3,
                    "synth_bene_cnt": 5,
                    "real_bene_grant_arch_distinct_cnt": 0,
                    "synth_bene_grant_arch_distinct_cnt": 0,
                    "real_bene_grant_and_arch_union_cnt": 3,
                    "synth_bene_grant_and_arch_union_cnt": 5,
                }
            }
        )
        validate_apps_dict.update(
            {
                "app1": {
                    "active": [True],
                    "require_demographic_scopes": [True],
                    "real_bene_cnt": 5,
                    "synth_bene_cnt": 2,
                    "real_bene_grant_arch_distinct_cnt": 0,
                    "synth_bene_grant_arch_distinct_cnt": 0,
                    "real_bene_grant_and_arch_union_cnt": 5,
                    "synth_bene_grant_and_arch_union_cnt": 2,
                }
            }
        )

        self._validate_global_state_per_app_metrics_log(validate_apps_dict)

        """
        TEST #2: Adds the following:
          2x synth benes to app3
          app3 set to not require demographic scopes and in-active
        """
        # Create 2x synth benes -40000000000000 thru -40000000000001 connected to app3
        app, ac_dict = self._create_range_users_app_token_grant(
            start_fhir_id="-4000000000000", count=2, app_name="app2"
        )

        # Set user_app2 to not require demographic scopes
        app.require_demographic_scopes = False
        app.active = False
        app.save()

        call_command("log_global_state_metrics", stdout=StringIO(), stderr=StringIO())

        self._validate_global_state_metrics_log(
            {
                "real_bene_cnt": 8,
                "synth_bene_cnt": 9,
                "real_bene_grant_cnt": 8,
                "synth_bene_grant_cnt": 9,
                "real_bene_token_distinct_cnt": 8,
                "synth_bene_token_distinct_cnt": 9,
                "real_bene_grant_distinct_cnt": 8,
                "synth_bene_grant_distinct_cnt": 9,
                "real_bene_grant_arch_distinct_cnt": 0,
                "synth_bene_grant_arch_distinct_cnt": 0,
                "real_bene_grant_and_arch_union_cnt": 8,
                "synth_bene_grant_and_arch_union_cnt": 9,
                "global_apps_active_cnt": 2,
                "global_apps_inactive_cnt": 1,
                "global_apps_require_demographic_scopes_cnt": 2,
            }
        )

        # NOTE: No dict changes needed for app0 & app1, just app2 below.
        validate_apps_dict.update(
            {
                "app2": {
                    "active": [False],
                    "require_demographic_scopes": [False],
                    "real_bene_cnt": 0,
                    "synth_bene_cnt": 2,
                    "real_bene_grant_arch_distinct_cnt": 0,
                    "synth_bene_grant_arch_distinct_cnt": 0,
                    "real_bene_grant_and_arch_union_cnt": 0,
                    "synth_bene_grant_and_arch_union_cnt": 2,
                }
            }
        )

        self._validate_global_state_per_app_metrics_log(validate_apps_dict)

        """
        TEST #3: Revokes grants from the list (2x synth from app0 & 3x real from app1)
                 This simulates a bene pressing the DENY button on the consent page.
                 The crosswalk records remain, but data access grants are removed.
                 NOTE:  The real_bene_cnt and synth_bene_cnt are crosswalk counts.
        """
        for app, user in remove_grant_access_list:
            print("--- Revoking:  ", app, " - ", user)
            remove_application_user_pair_tokens_data_access(app, user)

        call_command("log_global_state_metrics", stdout=StringIO(), stderr=StringIO())

        self._validate_global_state_metrics_log(
            {
                "real_bene_cnt": 8,
                "synth_bene_cnt": 9,
                "real_bene_grant_cnt": 6,
                "synth_bene_grant_cnt": 6,
                "real_bene_token_distinct_cnt": 6,
                "synth_bene_token_distinct_cnt": 6,
                "real_bene_grant_distinct_cnt": 6,
                "synth_bene_grant_distinct_cnt": 6,
                "real_bene_grant_arch_distinct_cnt": 2,
                "synth_bene_grant_arch_distinct_cnt": 3,
                "real_bene_grant_and_arch_union_cnt": 8,
                "synth_bene_grant_and_arch_union_cnt": 9,
                "global_apps_active_cnt": 2,
                "global_apps_inactive_cnt": 1,
                "global_apps_require_demographic_scopes_cnt": 2,
            }
        )

        # Validate per app count changes
        validate_apps_dict["app0"]["synth_bene_cnt"] = 2
        validate_apps_dict["app0"]["synth_bene_grant_arch_distinct_cnt"] = 3
        validate_apps_dict["app0"]["synth_bene_grant_and_arch_union_cnt"] = 5

        validate_apps_dict["app1"]["real_bene_cnt"] = 3
        validate_apps_dict["app1"]["real_bene_grant_arch_distinct_cnt"] = 2
        validate_apps_dict["app1"]["real_bene_grant_and_arch_union_cnt"] = 5

        self._validate_global_state_per_app_metrics_log(validate_apps_dict)

        """
        TEST #4:
            Create overlappiing benes connected to app0, app1 and app3
            with 7x synth and 10x real benes.
        """
        print(
            "================================================================================================="
        )
        print(
            "=======================TEST #4==================================================================="
        )
        print(
            "================================================================================================="
        )
        # Create 7x synth benes -60000000000000 thru -60000000000006 connected to app0, app1 and app3
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="-6000000000000", count=7, app_name="app0"
        )
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="-6000000000000", count=7, app_name="app1"
        )
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="-6000000000000", count=7, app_name="app3"
        )

        # Create 10x real benes 60000000000000 thru 60000000000009 connected to app0, app1 and app3
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="6000000000000", count=10, app_name="app0"
        )
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="6000000000000", count=10, app_name="app1"
        )
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="6000000000000", count=10, app_name="app3"
        )

        call_command("log_global_state_metrics", stdout=StringIO(), stderr=StringIO())

        self._validate_global_state_metrics_log(
            {
                "real_bene_cnt": 18,
                "synth_bene_cnt": 16,
                "real_bene_grant_cnt": 36,
                "synth_bene_grant_cnt": 27,
                "real_bene_token_distinct_cnt": 16,
                "synth_bene_token_distinct_cnt": 13,
                "real_bene_grant_distinct_cnt": 16,
                "synth_bene_grant_distinct_cnt": 13,
                "real_bene_grant_arch_distinct_cnt": 2,
                "synth_bene_grant_arch_distinct_cnt": 3,
                "real_bene_grant_and_arch_union_cnt": 18,
                "synth_bene_grant_and_arch_union_cnt": 16,
                "global_apps_active_cnt": 3,
                "global_apps_inactive_cnt": 1,
                "global_apps_require_demographic_scopes_cnt": 3,
            }
        )

        # Validate per app count changes
        validate_apps_dict["app0"]["synth_bene_cnt"] = 9
        validate_apps_dict["app0"]["synth_bene_grant_arch_distinct_cnt"] = 3
        validate_apps_dict["app0"]["synth_bene_grant_and_arch_union_cnt"] = 12
        validate_apps_dict["app0"]["real_bene_cnt"] = 13
        validate_apps_dict["app0"]["real_bene_grant_arch_distinct_cnt"] = 0
        validate_apps_dict["app0"]["real_bene_grant_and_arch_union_cnt"] = 13

        validate_apps_dict["app1"]["synth_bene_cnt"] = 9
        validate_apps_dict["app1"]["synth_bene_grant_arch_distinct_cnt"] = 0
        validate_apps_dict["app1"]["synth_bene_grant_and_arch_union_cnt"] = 9
        validate_apps_dict["app1"]["real_bene_cnt"] = 13
        validate_apps_dict["app1"]["real_bene_grant_arch_distinct_cnt"] = 2
        validate_apps_dict["app1"]["real_bene_grant_and_arch_union_cnt"] = 15

        validate_apps_dict.update(
            {
                "app3": {
                    "active": [True],
                    "require_demographic_scopes": [True],
                    "real_bene_cnt": 10,
                    "synth_bene_cnt": 7,
                    "real_bene_grant_arch_distinct_cnt": 0,
                    "synth_bene_grant_arch_distinct_cnt": 0,
                    "real_bene_grant_and_arch_union_cnt": 10,
                    "synth_bene_grant_and_arch_union_cnt": 7,
                }
            }
        )

        self._validate_global_state_per_app_metrics_log(validate_apps_dict)
