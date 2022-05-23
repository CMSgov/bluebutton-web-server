import copy
import json
import jsonschema

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test.client import Client
from django.utils import timezone
from jsonschema import validate
from io import StringIO
from oauth2_provider.models import get_access_token_model, get_application_model

from apps.dot_ext.utils import (
    remove_application_user_pair_tokens_data_access,
)
from apps.fhir.bluebutton.models import Crosswalk, ArchivedCrosswalk
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

# Set to True to enable console report for management command calls.
CALL_MANAGEMENT_COMMAND_REPORT_TO_CONSOLE = False

# DEBUG flag to enable extra info in tests
TEST_DEBUG = False


class TestLoggersGlobalMetricsManagementCommand(BaseApiTest):
    def setUp(self):
        # Setup the RequestFactory
        self.client = Client()
        self._redirect_loggers()

    def tearDown(self):
        self._cleanup_logger()

    def _call_management_command_log_global_state_metrics(self, report_to_console=CALL_MANAGEMENT_COMMAND_REPORT_TO_CONSOLE):
        """
        Method to call the management command in tests.

        Args:
            report_to_console =
                True - Include command report in output. Useful for debugging.
                False - Exclude command report in output.
        """
        if report_to_console:
            call_command("log_global_state_metrics", stdout=StringIO(), stderr=StringIO())
        else:
            call_command("log_global_state_metrics", "--no-report", stdout=StringIO(), stderr=StringIO())

    def _debug_show_value_differences(self, dict_a, dict_b):
        """
        Show differences between dict_a and dict_b for debugging.
        """
        print("")
        print("=============_debug_show_value_differences()=============")
        for key in dict_b:
            # Skip these keys:
            if dict_a:
                a = dict_a.get(key, None)
            else:
                a = None
            b = dict_b.get(key, None)
            if a != b and type(b) == int:
                print("\"{}\": {},  # {} -> {}".format(key, b, a, b))
        print("=========================================================")
        print("")

    def _get_log_content(self, logger_name):
        return self._collect_logs().get(logger_name)

    def _validateJsonSchema(self, schema, content):
        try:
            validate(instance=content, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            # Show error info to help with debugging
            print("===")
            print("jsonschema.exceptions.ValidationError: ", e)
            print("")
            print("CONTENT:  ", content)
            print("")
            print("To match SCHEMA:  ", schema)
            print("===")
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

        # last_log_dict for debugging
        last_log_dict = None
        log_dict = None

        # Get last global_state_metrics log entry
        for line in log_content_buf:
            line_dict = json.loads(line)
            if line_dict["type"] == "global_state_metrics":
                last_log_dict = log_dict
                log_dict = line_dict

        if TEST_DEBUG:
            self._debug_show_value_differences(last_log_dict, log_dict)

        # Update Json Schema for assert
        fields_list = [
            "real_bene_cnt",
            "synth_bene_cnt",
            "crosswalk_real_bene_count",
            "crosswalk_synthetic_bene_count",
            "crosswalk_table_count",
            "crosswalk_archived_table_count",
            "grant_real_bene_count",
            "grant_synthetic_bene_count",
            "grant_table_count",
            "grant_archived_table_count",
            "grant_real_bene_deduped_count",
            "grant_synthetic_bene_deduped_count",
            "grantarchived_real_bene_deduped_count",
            "grantarchived_synthetic_bene_deduped_count",
            "grant_and_archived_real_bene_deduped_count",
            "grant_and_archived_synthetic_bene_deduped_count",
            "token_real_bene_deduped_count",
            "token_synthetic_bene_deduped_count",
            "token_table_count",
            "token_archived_table_count",
            "token_real_bene_app_pair_deduped_count",
            "token_synthetic_bene_app_pair_deduped_count",
            "global_apps_active_cnt",
            "global_apps_inactive_cnt",
            "global_apps_require_demographic_scopes_cnt",
            "global_developer_count",
            "global_developer_with_registered_app_count",
            "global_developer_with_first_api_call_count",
            "global_developer_distinct_organization_name_count",
            "global_beneficiary_count",
            "global_beneficiary_real_count",
            "global_beneficiary_synthetic_count",
            "global_beneficiary_grant_count",
            "global_beneficiary_real_grant_count",
            "global_beneficiary_synthetic_grant_count",
            "global_beneficiary_grant_archived_count",
            "global_beneficiary_real_grant_archived_count",
            "global_beneficiary_synthetic_grant_archived_count",
            "global_beneficiary_grant_or_archived_count",
            "global_beneficiary_real_grant_or_archived_count",
            "global_beneficiary_synthetic_grant_or_archived_count",
            "global_beneficiary_grant_and_archived_count",
            "global_beneficiary_real_grant_and_archived_count",
            "global_beneficiary_synthetic_grant_and_archived_count",
            "global_beneficiary_grant_not_archived_count",
            "global_beneficiary_real_grant_not_archived_count",
            "global_beneficiary_synthetic_grant_not_archived_count",
            "global_beneficiary_archived_not_grant_count",
            "global_beneficiary_real_archived_not_grant_count",
            "global_beneficiary_synthetic_archived_not_grant_count",
            "global_beneficiary_real_grant_to_apps_eq_1_count",
            "global_beneficiary_synthetic_grant_to_apps_eq_1_count",
            "global_beneficiary_real_grant_to_apps_eq_2_count",
            "global_beneficiary_synthetic_grant_to_apps_eq_2_count",
            "global_beneficiary_real_grant_to_apps_eq_3_count",
            "global_beneficiary_synthetic_grant_to_apps_eq_3_count",
            "global_beneficiary_real_grant_to_apps_eq_4thru5_count",
            "global_beneficiary_synthetic_grant_to_apps_eq_4thru5_count",
            "global_beneficiary_real_grant_to_apps_eq_6thru8_count",
            "global_beneficiary_synthetic_grant_to_apps_eq_6thru8_count",
            "global_beneficiary_real_grant_to_apps_eq_9thru13_count",
            "global_beneficiary_synthetic_grant_to_apps_eq_9thru13_count",
            "global_beneficiary_real_grant_to_apps_gt_13_count",
            "global_beneficiary_synthetic_grant_to_apps_gt_13_count",
            "global_beneficiary_real_grant_archived_to_apps_eq_1_count",
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_1_count",
            "global_beneficiary_real_grant_archived_to_apps_eq_2_count",
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_2_count",
            "global_beneficiary_real_grant_archived_to_apps_eq_3_count",
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_3_count",
            "global_beneficiary_real_grant_archived_to_apps_eq_4thru5_count",
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_4thru5_count",
            "global_beneficiary_real_grant_archived_to_apps_eq_6thru8_count",
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_6thru8_count",
            "global_beneficiary_real_grant_archived_to_apps_eq_9thru13_count",
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_9thru13_count",
            "global_beneficiary_real_grant_archived_to_apps_gt_13_count",
            "global_beneficiary_synthetic_grant_archived_to_apps_gt_13_count",
            "global_beneficiary_app_pair_grant_count",
            "global_beneficiary_app_pair_real_grant_count",
            "global_beneficiary_app_pair_synthetic_grant_count",
            "global_beneficiary_app_pair_grant_archived_count",
            "global_beneficiary_app_pair_real_grant_archived_count",
            "global_beneficiary_app_pair_synthetic_grant_archived_count",
            "global_beneficiary_app_pair_grant_vs_archived_difference_total_count",
            "global_beneficiary_app_pair_real_grant_vs_archived_difference_total_count",
            "global_beneficiary_app_pair_synthetic_grant_vs_archived_difference_total_count",
            "global_beneficiary_app_pair_archived_vs_grant_difference_total_count",
            "global_beneficiary_app_pair_real_archived_vs_grant_difference_total_count",
            "global_beneficiary_app_pair_synthetic_archived_vs_grant_difference_total_count",
        ]

        for f in fields_list:
            TEST_GLOBAL_STATE_METRICS_LOG_SCHEMA["properties"][f]["enum"] = [
                validate_dict[f]
            ]

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

            # Update Json Schema for assert
            fields_list = [
                "active",
                "require_demographic_scopes",
                "real_bene_cnt",
                "synth_bene_cnt",
                "grant_real_bene_count",
                "grant_synthetic_bene_count",
                "grant_table_count",
                "grant_archived_table_count",
                "grantarchived_real_bene_deduped_count",
                "grantarchived_synthetic_bene_deduped_count",
                "grant_and_archived_real_bene_deduped_count",
                "grant_and_archived_synthetic_bene_deduped_count",
                "token_real_bene_count",
                "token_synthetic_bene_count",
                "token_table_count",
                "token_archived_table_count",
            ]

            # Update Json Schema
            TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"]["name"][
                "pattern"
            ] = app_name

            for f in fields_list:
                if (
                    TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"][f][
                        "type"
                    ]
                    == "boolean"
                ):
                    TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"][f][
                        "enum"
                    ] = validate_apps_dict[app_name][f]
                else:
                    TEST_GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"][f][
                        "enum"
                    ] = [validate_apps_dict[app_name][f]]

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
            start_fhir_id="-2000000000000", count=5, app_name="app0",
            app_user_organization="app0-org"
        )

        # Add app & user tuples to remove in TEST #3
        remove_grant_access_list.append((app, user_dict["-20000000000002"]))
        remove_grant_access_list.append((app, user_dict["-20000000000003"]))
        remove_grant_access_list.append((app, user_dict["-20000000000004"]))

        # Create 3x real benes 40000000000000 thru 40000000000002 connected to app0
        self._create_range_users_app_token_grant(
            start_fhir_id="4000000000000", count=3, app_name="app0",
            app_user_organization="app0-org"
        )

        # Create 2x synth benes -30000000000000 thru -30000000000001 connected to app1
        self._create_range_users_app_token_grant(
            start_fhir_id="-3000000000000", count=2, app_name="app1",
            app_user_organization="app1-org"
        )

        # Create 5x real benes 50000000000000 thru 50000000000004 connected to app1
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="5000000000000", count=5, app_name="app1",
            app_user_organization="app1-org"
        )

        # Add app & user tuples to remove in TEST #3
        remove_grant_access_list.append((app, user_dict["50000000000001"]))
        remove_grant_access_list.append((app, user_dict["50000000000003"]))

        # Create users / crosswalks that DO NOT have grants & access tokens (2x synth and 3x real).
        self._create_user(
            "extra_crosswalk_synth_user01@example.com",
            "xxx123",
            "-90000000000001",
            "xxxExtraHicnSynth01xxx",
            None,
            "BEN",
        )
        self._create_user(
            "extra_crosswalk_synth_user02@example.com",
            "xxx123",
            "-90000000000002",
            "xxxExtraHicnSynth02xxx",
            None,
            "BEN",
        )
        self._create_user(
            "extra_crosswalk_real_user01@example.com",
            "xxx123",
            "90000000000001",
            "xxxExtraHicnReal01xxx",
            None,
            "BEN",
        )
        self._create_user(
            "extra_crosswalk_real_user02@example.com",
            "xxx123",
            "90000000000002",
            "xxxExtraHicnReal02xxx",
            None,
            "BEN",
        )
        self._create_user(
            "extra_crosswalk_real_user03@example.com",
            "xxx123",
            "90000000000003",
            "xxxExtraHicnReal03xxx",
            None,
            "BEN",
        )

        self._call_management_command_log_global_state_metrics()

        # Setup inital dict used for global state metrics validation.
        validate_global_dict = {
            "real_bene_cnt": 11,
            "synth_bene_cnt": 9,
            "crosswalk_real_bene_count": 11,
            "crosswalk_synthetic_bene_count": 9,
            "crosswalk_table_count": 20,
            "crosswalk_archived_table_count": 0,
            "grant_real_bene_count": 8,
            "grant_synthetic_bene_count": 7,
            "grant_table_count": 15,
            "grant_archived_table_count": 0,
            "grant_real_bene_deduped_count": 8,
            "grant_synthetic_bene_deduped_count": 7,
            "grantarchived_real_bene_deduped_count": 0,
            "grantarchived_synthetic_bene_deduped_count": 0,
            "grant_and_archived_real_bene_deduped_count": 8,
            "grant_and_archived_synthetic_bene_deduped_count": 7,
            "token_real_bene_deduped_count": 8,
            "token_synthetic_bene_deduped_count": 7,
            "token_table_count": 15,
            "token_archived_table_count": 0,
            "token_real_bene_app_pair_deduped_count": 8,
            "token_synthetic_bene_app_pair_deduped_count": 7,
            "global_apps_active_cnt": 2,
            "global_apps_inactive_cnt": 0,
            "global_apps_require_demographic_scopes_cnt": 2,
            "global_developer_count": 2,
            "global_developer_with_registered_app_count": 2,
            "global_developer_with_first_api_call_count": 0,
            "global_developer_distinct_organization_name_count": 2,
            "global_beneficiary_count": 20,
            "global_beneficiary_real_count": 11,
            "global_beneficiary_synthetic_count": 9,
            "global_beneficiary_grant_count": 15,
            "global_beneficiary_real_grant_count": 8,
            "global_beneficiary_synthetic_grant_count": 7,
            "global_beneficiary_grant_archived_count": 0,
            "global_beneficiary_real_grant_archived_count": 0,
            "global_beneficiary_synthetic_grant_archived_count": 0,
            "global_beneficiary_grant_or_archived_count": 15,
            "global_beneficiary_real_grant_or_archived_count": 8,
            "global_beneficiary_synthetic_grant_or_archived_count": 7,
            "global_beneficiary_grant_and_archived_count": 0,
            "global_beneficiary_real_grant_and_archived_count": 0,
            "global_beneficiary_synthetic_grant_and_archived_count": 0,
            "global_beneficiary_grant_not_archived_count": 15,
            "global_beneficiary_real_grant_not_archived_count": 8,
            "global_beneficiary_synthetic_grant_not_archived_count": 7,
            "global_beneficiary_archived_not_grant_count": 0,
            "global_beneficiary_real_archived_not_grant_count": 0,
            "global_beneficiary_synthetic_archived_not_grant_count": 0,
            "global_beneficiary_real_grant_to_apps_eq_1_count": 8,
            "global_beneficiary_synthetic_grant_to_apps_eq_1_count": 7,
            "global_beneficiary_real_grant_to_apps_eq_2_count": 0,
            "global_beneficiary_synthetic_grant_to_apps_eq_2_count": 0,
            "global_beneficiary_real_grant_to_apps_eq_3_count": 0,
            "global_beneficiary_synthetic_grant_to_apps_eq_3_count": 0,
            "global_beneficiary_real_grant_to_apps_eq_4thru5_count": 0,
            "global_beneficiary_synthetic_grant_to_apps_eq_4thru5_count": 0,
            "global_beneficiary_real_grant_to_apps_eq_6thru8_count": 0,
            "global_beneficiary_synthetic_grant_to_apps_eq_6thru8_count": 0,
            "global_beneficiary_real_grant_to_apps_eq_9thru13_count": 0,
            "global_beneficiary_synthetic_grant_to_apps_eq_9thru13_count": 0,
            "global_beneficiary_real_grant_to_apps_gt_13_count": 0,
            "global_beneficiary_synthetic_grant_to_apps_gt_13_count": 0,
            "global_beneficiary_real_grant_archived_to_apps_eq_1_count": 0,
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_1_count": 0,
            "global_beneficiary_real_grant_archived_to_apps_eq_2_count": 0,
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_2_count": 0,
            "global_beneficiary_real_grant_archived_to_apps_eq_3_count": 0,
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_3_count": 0,
            "global_beneficiary_real_grant_archived_to_apps_eq_4thru5_count": 0,
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_4thru5_count": 0,
            "global_beneficiary_real_grant_archived_to_apps_eq_6thru8_count": 0,
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_6thru8_count": 0,
            "global_beneficiary_real_grant_archived_to_apps_eq_9thru13_count": 0,
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_9thru13_count": 0,
            "global_beneficiary_real_grant_archived_to_apps_gt_13_count": 0,
            "global_beneficiary_synthetic_grant_archived_to_apps_gt_13_count": 0,
            "global_beneficiary_app_pair_grant_count": 15,
            "global_beneficiary_app_pair_real_grant_count": 8,
            "global_beneficiary_app_pair_synthetic_grant_count": 7,
            "global_beneficiary_app_pair_grant_archived_count": 0,
            "global_beneficiary_app_pair_real_grant_archived_count": 0,
            "global_beneficiary_app_pair_synthetic_grant_archived_count": 0,
            "global_beneficiary_app_pair_grant_vs_archived_difference_total_count": 15,
            "global_beneficiary_app_pair_real_grant_vs_archived_difference_total_count": 8,
            "global_beneficiary_app_pair_synthetic_grant_vs_archived_difference_total_count": 7,
            "global_beneficiary_app_pair_archived_vs_grant_difference_total_count": 0,
            "global_beneficiary_app_pair_real_archived_vs_grant_difference_total_count": 0,
            "global_beneficiary_app_pair_synthetic_archived_vs_grant_difference_total_count": 0
        }
        self._validate_global_state_metrics_log(validate_global_dict)

        validate_apps_dict.update(
            {
                "app0": {
                    "active": [True],
                    "require_demographic_scopes": [True],
                    "real_bene_cnt": 3,
                    "synth_bene_cnt": 5,
                    "grant_real_bene_count": 3,
                    "grant_synthetic_bene_count": 5,
                    "grant_table_count": 8,
                    "grant_archived_table_count": 0,
                    "grantarchived_real_bene_deduped_count": 0,
                    "grantarchived_synthetic_bene_deduped_count": 0,
                    "grant_and_archived_real_bene_deduped_count": 3,
                    "grant_and_archived_synthetic_bene_deduped_count": 5,
                    "token_real_bene_count": 3,
                    "token_synthetic_bene_count": 5,
                    "token_table_count": 8,
                    "token_archived_table_count": 0,
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
                    "grant_table_count": 7,
                    "grant_archived_table_count": 0,
                    "grant_real_bene_count": 5,
                    "grant_synthetic_bene_count": 2,
                    "grantarchived_real_bene_deduped_count": 0,
                    "grantarchived_synthetic_bene_deduped_count": 0,
                    "grant_and_archived_real_bene_deduped_count": 5,
                    "grant_and_archived_synthetic_bene_deduped_count": 2,
                    "token_real_bene_count": 5,
                    "token_synthetic_bene_count": 2,
                    "token_table_count": 7,
                    "token_archived_table_count": 0,
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
            start_fhir_id="-4000000000000", count=2, app_name="app2",
            app_user_organization="app2-org"
        )

        # Set user_app2 to not require demographic scopes
        app.require_demographic_scopes = False
        app.active = False
        app.save()

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "synth_bene_cnt": 11,  # 9 -> 11
            "crosswalk_synthetic_bene_count": 11,  # 9 -> 11
            "crosswalk_table_count": 22,  # 20 -> 22
            "grant_synthetic_bene_count": 9,  # 7 -> 9
            "grant_table_count": 17,  # 15 -> 17
            "grant_synthetic_bene_deduped_count": 9,  # 7 -> 9
            "grant_and_archived_synthetic_bene_deduped_count": 9,  # 7 -> 9
            "token_synthetic_bene_deduped_count": 9,  # 7 -> 9
            "token_table_count": 17,  # 15 -> 17
            "token_synthetic_bene_app_pair_deduped_count": 9,  # 7 -> 9
            "global_apps_inactive_cnt": 1,  # 0 -> 1
            "global_developer_count": 3,  # 2 -> 3
            "global_developer_with_registered_app_count": 3,  # 2 -> 3
            "global_developer_distinct_organization_name_count": 3,  # 2 -> 3
            "global_beneficiary_count": 22,  # 20 -> 22
            "global_beneficiary_synthetic_count": 11,  # 9 -> 11
            "global_beneficiary_grant_count": 17,  # 15 -> 17
            "global_beneficiary_synthetic_grant_count": 9,  # 7 -> 9
            "global_beneficiary_grant_or_archived_count": 17,  # 15 -> 17
            "global_beneficiary_synthetic_grant_or_archived_count": 9,  # 7 -> 9
            "global_beneficiary_grant_not_archived_count": 17,  # 15 -> 17
            "global_beneficiary_synthetic_grant_not_archived_count": 9,  # 7 -> 9
            "global_beneficiary_synthetic_grant_to_apps_eq_1_count": 9,  # 7 -> 9
            "global_beneficiary_app_pair_grant_count": 17,  # 15 -> 17
            "global_beneficiary_app_pair_synthetic_grant_count": 9,  # 7 -> 9
            "global_beneficiary_app_pair_grant_vs_archived_difference_total_count": 17,  # 15 -> 17
            "global_beneficiary_app_pair_synthetic_grant_vs_archived_difference_total_count": 9,  # 7 -> 9
        })
        self._validate_global_state_metrics_log(validate_global_dict)

        # NOTE: No dict changes needed for app0 & app1, just app2 below.
        validate_apps_dict.update(
            {
                "app2": {
                    "active": [False],
                    "require_demographic_scopes": [False],
                    "real_bene_cnt": 0,
                    "synth_bene_cnt": 2,
                    "grant_table_count": 2,
                    "grant_archived_table_count": 0,
                    "grant_real_bene_count": 0,
                    "grant_synthetic_bene_count": 2,
                    "grantarchived_real_bene_deduped_count": 0,
                    "grantarchived_synthetic_bene_deduped_count": 0,
                    "grant_and_archived_real_bene_deduped_count": 0,
                    "grant_and_archived_synthetic_bene_deduped_count": 2,
                    "token_real_bene_count": 0,
                    "token_synthetic_bene_count": 2,
                    "token_table_count": 2,
                    "token_archived_table_count": 0,
                }
            }
        )

        self._validate_global_state_per_app_metrics_log(validate_apps_dict)

        """
        TEST #3: Revokes grants from the list (3x synth from app0 & 2x real from app1)
                 This simulates a bene pressing the DENY button on the consent page.
                 The crosswalk records remain, but data access grants are removed.
                 NOTE:  The real_bene_cnt and synth_bene_cnt are crosswalk counts.
                        These are replaced by crosswalk_<real/synthetic>_bene_count
                        namings and should be removed in the future (after dashboards, etc.
                        have been updated).
        """
        for app, user in remove_grant_access_list:
            remove_application_user_pair_tokens_data_access(app, user)

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "grant_real_bene_count": 6,  # 8 -> 6
            "grant_synthetic_bene_count": 6,  # 9 -> 6
            "grant_table_count": 12,  # 17 -> 12
            "grant_archived_table_count": 5,  # 0 -> 5
            "grant_real_bene_deduped_count": 6,  # 8 -> 6
            "grant_synthetic_bene_deduped_count": 6,  # 9 -> 6
            "grantarchived_real_bene_deduped_count": 2,  # 0 -> 2
            "grantarchived_synthetic_bene_deduped_count": 3,  # 0 -> 3
            "token_real_bene_deduped_count": 6,  # 8 -> 6
            "token_synthetic_bene_deduped_count": 6,  # 9 -> 6
            "token_table_count": 12,  # 17 -> 12
            "token_archived_table_count": 5,  # 0 -> 5
            "token_real_bene_app_pair_deduped_count": 6,  # 8 -> 6
            "token_synthetic_bene_app_pair_deduped_count": 6,  # 9 -> 6
            "global_beneficiary_grant_count": 12,  # 17 -> 12
            "global_beneficiary_real_grant_count": 6,  # 8 -> 6
            "global_beneficiary_synthetic_grant_count": 6,  # 9 -> 6
            "global_beneficiary_grant_archived_count": 5,  # 0 -> 5
            "global_beneficiary_real_grant_archived_count": 2,  # 0 -> 2
            "global_beneficiary_synthetic_grant_archived_count": 3,  # 0 -> 3
            "global_beneficiary_grant_not_archived_count": 12,  # 17 -> 12
            "global_beneficiary_real_grant_not_archived_count": 6,  # 8 -> 6
            "global_beneficiary_synthetic_grant_not_archived_count": 6,  # 9 -> 6
            "global_beneficiary_archived_not_grant_count": 5,  # 0 -> 5
            "global_beneficiary_real_archived_not_grant_count": 2,  # 0 -> 2
            "global_beneficiary_synthetic_archived_not_grant_count": 3,  # 0 -> 3
            "global_beneficiary_real_grant_to_apps_eq_1_count": 6,  # 8 -> 6
            "global_beneficiary_synthetic_grant_to_apps_eq_1_count": 6,  # 9 -> 6
            "global_beneficiary_real_grant_archived_to_apps_eq_1_count": 2,  # 0 -> 2
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_1_count": 3,  # 0 -> 3
            "global_beneficiary_app_pair_grant_count": 12,  # 17 -> 12
            "global_beneficiary_app_pair_real_grant_count": 6,  # 8 -> 6
            "global_beneficiary_app_pair_synthetic_grant_count": 6,  # 9 -> 6
            "global_beneficiary_app_pair_grant_archived_count": 5,  # 0 -> 5
            "global_beneficiary_app_pair_real_grant_archived_count": 2,  # 0 -> 2
            "global_beneficiary_app_pair_synthetic_grant_archived_count": 3,  # 0 -> 3
            "global_beneficiary_app_pair_grant_vs_archived_difference_total_count": 12,  # 17 -> 12
            "global_beneficiary_app_pair_real_grant_vs_archived_difference_total_count": 6,  # 8 -> 6
            "global_beneficiary_app_pair_synthetic_grant_vs_archived_difference_total_count": 6,  # 9 -> 6
            "global_beneficiary_app_pair_archived_vs_grant_difference_total_count": 5,  # 0 -> 5
            "global_beneficiary_app_pair_real_archived_vs_grant_difference_total_count": 2,  # 0 -> 2
            "global_beneficiary_app_pair_synthetic_archived_vs_grant_difference_total_count": 3,  # 0 -> 3
        })
        self._validate_global_state_metrics_log(validate_global_dict)

        # Validate per app count changes
        validate_apps_dict["app0"]["synth_bene_cnt"] = 2
        validate_apps_dict["app0"]["grant_synthetic_bene_count"] = 2
        validate_apps_dict["app0"]["grant_table_count"] = 5
        validate_apps_dict["app0"]["grant_archived_table_count"] = 3
        validate_apps_dict["app0"]["grantarchived_synthetic_bene_deduped_count"] = 3
        validate_apps_dict["app0"][
            "grant_and_archived_synthetic_bene_deduped_count"
        ] = 5
        validate_apps_dict["app0"]["token_synthetic_bene_count"] = 2
        validate_apps_dict["app0"]["token_table_count"] = 5
        validate_apps_dict["app0"]["token_archived_table_count"] = 3

        validate_apps_dict["app1"]["real_bene_cnt"] = 3
        validate_apps_dict["app1"]["grant_real_bene_count"] = 3
        validate_apps_dict["app1"]["grant_table_count"] = 5
        validate_apps_dict["app1"]["grant_archived_table_count"] = 2

        validate_apps_dict["app1"]["grantarchived_real_bene_deduped_count"] = 2
        validate_apps_dict["app1"]["grant_and_archived_real_bene_deduped_count"] = 5
        validate_apps_dict["app1"]["token_real_bene_count"] = 3
        validate_apps_dict["app1"]["token_table_count"] = 5
        validate_apps_dict["app1"]["token_archived_table_count"] = 2

        self._validate_global_state_per_app_metrics_log(validate_apps_dict)

        """
        TEST #4:
            Create overlappiing benes connected to app0, app1 and app3
            with 7x synth and 10x real benes.
        """
        # Create 7x synth benes -60000000000000 thru -60000000000006 connected to app0, app1 and app3
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="-6000000000000", count=7, app_name="app0",
            app_user_organization="app0-org"
        )
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="-6000000000000", count=7, app_name="app1",
            app_user_organization="app1-org"
        )

        # Keep user_dict for TEST #5
        save_synth_user_dict = user_dict

        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="-6000000000000", count=7, app_name="app3",
            app_user_organization="app3-org"
        )

        # Create 10x real benes 60000000000000 thru 60000000000009 connected to app0, app1 and app3
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="6000000000000", count=10, app_name="app0",
            app_user_organization="app0-org"
        )
        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="6000000000000", count=10, app_name="app1",
            app_user_organization="app1-org"
        )

        # Keep user_dict for TEST #6
        save_real_user_dict = user_dict

        app, user_dict = self._create_range_users_app_token_grant(
            start_fhir_id="6000000000000", count=10, app_name="app3",
            app_user_organization="app3-org"
        )

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "real_bene_cnt": 21,  # 11 -> 21
            "synth_bene_cnt": 18,  # 11 -> 18
            "crosswalk_real_bene_count": 21,  # 11 -> 21
            "crosswalk_synthetic_bene_count": 18,  # 11 -> 18
            "crosswalk_table_count": 39,  # 22 -> 39
            "grant_real_bene_count": 36,  # 6 -> 36
            "grant_synthetic_bene_count": 27,  # 6 -> 27
            "grant_table_count": 63,  # 12 -> 63
            "grant_real_bene_deduped_count": 16,  # 6 -> 16
            "grant_synthetic_bene_deduped_count": 13,  # 6 -> 13
            "grant_and_archived_real_bene_deduped_count": 18,  # 8 -> 18
            "grant_and_archived_synthetic_bene_deduped_count": 16,  # 9 -> 16
            "token_real_bene_deduped_count": 16,  # 6 -> 16
            "token_synthetic_bene_deduped_count": 13,  # 6 -> 13
            "token_table_count": 63,  # 12 -> 63
            "token_real_bene_app_pair_deduped_count": 36,  # 6 -> 36
            "token_synthetic_bene_app_pair_deduped_count": 27,  # 6 -> 27
            "global_apps_active_cnt": 3,  # 2 -> 3
            "global_apps_require_demographic_scopes_cnt": 3,  # 2 -> 3
            "global_developer_count": 4,  # 3 -> 4
            "global_developer_with_registered_app_count": 4,  # 3 -> 4
            "global_developer_distinct_organization_name_count": 4,  # 3 -> 4
            "global_beneficiary_count": 39,  # 22 -> 39
            "global_beneficiary_real_count": 21,  # 11 -> 21
            "global_beneficiary_synthetic_count": 18,  # 11 -> 18
            "global_beneficiary_grant_count": 29,  # 12 -> 29
            "global_beneficiary_real_grant_count": 16,  # 6 -> 16
            "global_beneficiary_synthetic_grant_count": 13,  # 6 -> 13
            "global_beneficiary_grant_or_archived_count": 34,  # 17 -> 34
            "global_beneficiary_real_grant_or_archived_count": 18,  # 8 -> 18
            "global_beneficiary_synthetic_grant_or_archived_count": 16,  # 9 -> 16
            "global_beneficiary_grant_not_archived_count": 29,  # 12 -> 29
            "global_beneficiary_real_grant_not_archived_count": 16,  # 6 -> 16
            "global_beneficiary_synthetic_grant_not_archived_count": 13,  # 6 -> 13
            "global_beneficiary_real_grant_to_apps_eq_3_count": 10,  # 0 -> 10
            "global_beneficiary_synthetic_grant_to_apps_eq_3_count": 7,  # 0 -> 7
            "global_beneficiary_app_pair_grant_count": 63,  # 12 -> 63
            "global_beneficiary_app_pair_real_grant_count": 36,  # 6 -> 36
            "global_beneficiary_app_pair_synthetic_grant_count": 27,  # 6 -> 27
            "global_beneficiary_app_pair_grant_vs_archived_difference_total_count": 63,  # 12 -> 63
            "global_beneficiary_app_pair_real_grant_vs_archived_difference_total_count": 36,  # 6 -> 36
            "global_beneficiary_app_pair_synthetic_grant_vs_archived_difference_total_count": 27,  # 6 -> 27
        })
        self._validate_global_state_metrics_log(validate_global_dict)

        # Validate per app count changes
        validate_apps_dict["app0"]["synth_bene_cnt"] = 9
        validate_apps_dict["app0"]["grant_synthetic_bene_count"] = 9
        validate_apps_dict["app0"]["grantarchived_synthetic_bene_deduped_count"] = 3
        validate_apps_dict["app0"][
            "grant_and_archived_synthetic_bene_deduped_count"
        ] = 12
        validate_apps_dict["app0"]["token_synthetic_bene_count"] = 9

        validate_apps_dict["app0"]["real_bene_cnt"] = 13
        validate_apps_dict["app0"]["grant_real_bene_count"] = 13
        validate_apps_dict["app0"]["grantarchived_real_bene_deduped_count"] = 0
        validate_apps_dict["app0"]["grant_and_archived_real_bene_deduped_count"] = 13

        validate_apps_dict["app0"]["grant_table_count"] = 22
        validate_apps_dict["app0"]["grant_archived_table_count"] = 3
        validate_apps_dict["app0"]["token_real_bene_count"] = 13
        validate_apps_dict["app0"]["token_table_count"] = 22
        validate_apps_dict["app0"]["token_archived_table_count"] = 3

        validate_apps_dict["app1"]["synth_bene_cnt"] = 9
        validate_apps_dict["app1"]["grant_synthetic_bene_count"] = 9
        validate_apps_dict["app1"]["grantarchived_synthetic_bene_deduped_count"] = 0
        validate_apps_dict["app1"][
            "grant_and_archived_synthetic_bene_deduped_count"
        ] = 9
        validate_apps_dict["app1"]["token_synthetic_bene_count"] = 9

        validate_apps_dict["app1"]["real_bene_cnt"] = 13
        validate_apps_dict["app1"]["grant_real_bene_count"] = 13
        validate_apps_dict["app1"]["grantarchived_real_bene_deduped_count"] = 2
        validate_apps_dict["app1"]["grant_and_archived_real_bene_deduped_count"] = 15
        validate_apps_dict["app1"]["token_real_bene_count"] = 13

        validate_apps_dict["app1"]["grant_table_count"] = 22
        validate_apps_dict["app1"]["grant_archived_table_count"] = 2
        validate_apps_dict["app1"]["token_table_count"] = 22
        validate_apps_dict["app1"]["token_archived_table_count"] = 2

        validate_apps_dict.update(
            {
                "app3": {
                    "active": [True],
                    "require_demographic_scopes": [True],
                    "real_bene_cnt": 10,
                    "synth_bene_cnt": 7,
                    "grant_real_bene_count": 10,
                    "grant_synthetic_bene_count": 7,
                    "grant_table_count": 17,
                    "grant_archived_table_count": 0,
                    "grantarchived_real_bene_deduped_count": 0,
                    "grantarchived_synthetic_bene_deduped_count": 0,
                    "grant_and_archived_real_bene_deduped_count": 10,
                    "grant_and_archived_synthetic_bene_deduped_count": 7,
                    "token_real_bene_count": 10,
                    "token_synthetic_bene_count": 7,
                    "token_table_count": 17,
                    "token_archived_table_count": 0,
                }
            }
        )

        self._validate_global_state_per_app_metrics_log(validate_apps_dict)

        """
        TEST #5:

        Test that crosswalk record with fhir_id = "" is not counted.

        NOTE: Due to a unique constraint on the fhir_id, there can only be one of these in the system.

        Setting one synth bene crosswalk fhir_id = "" should reduce synth counts by 1.
        """
        # Setting synth user crosswalk entry to fhir_id="" and archiving cw
        cw = Crosswalk.objects.get(user=save_synth_user_dict["-60000000000003"])
        ArchivedCrosswalk.create(cw)
        cw._fhir_id = ""
        cw.save()

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "synth_bene_cnt": 17,  # 18 -> 17
            "crosswalk_synthetic_bene_count": 17,  # 18 -> 17
            "crosswalk_archived_table_count": 1,  # 0 -> 1
            "grant_synthetic_bene_count": 24,  # 27 -> 24
            "grant_synthetic_bene_deduped_count": 12,  # 13 -> 12
            "grant_and_archived_synthetic_bene_deduped_count": 15,  # 16 -> 15
            "token_synthetic_bene_deduped_count": 12,  # 13 -> 12
            "token_synthetic_bene_app_pair_deduped_count": 24,  # 27 -> 24
            "global_beneficiary_synthetic_count": 17,  # 18 -> 17
            "global_beneficiary_synthetic_grant_count": 12,  # 13 -> 12
            "global_beneficiary_synthetic_grant_or_archived_count": 15,  # 16 -> 15
            "global_beneficiary_synthetic_grant_not_archived_count": 12,  # 13 -> 12
            "global_beneficiary_synthetic_token_count": 12,  # 13 -> 12
            "global_beneficiary_synthetic_token_or_archived_count": 15,  # 16 -> 15
            "global_beneficiary_synthetic_token_not_archived_count": 12,  # 13 -> 12
            "global_beneficiary_synthetic_grant_to_apps_eq_3_count": 6,  # 7 -> 6
            "global_beneficiary_app_pair_synthetic_grant_count": 24,  # 27 -> 24
            "global_beneficiary_app_pair_synthetic_grant_vs_archived_difference_total_count": 24,  # 27 -> 24
        })
        self._validate_global_state_metrics_log(validate_global_dict)

        # Validate per app count changes
        validate_apps_dict["app0"]["synth_bene_cnt"] = 8
        validate_apps_dict["app0"]["grant_synthetic_bene_count"] = 8
        validate_apps_dict["app0"][
            "grant_and_archived_synthetic_bene_deduped_count"
        ] = 11
        validate_apps_dict["app0"]["token_synthetic_bene_count"] = 8
        validate_apps_dict["app0"]["grant_table_count"] = 22
        validate_apps_dict["app0"]["token_table_count"] = 22

        validate_apps_dict["app1"]["synth_bene_cnt"] = 8
        validate_apps_dict["app1"]["grant_synthetic_bene_count"] = 8
        validate_apps_dict["app1"][
            "grant_and_archived_synthetic_bene_deduped_count"
        ] = 8
        validate_apps_dict["app1"]["token_synthetic_bene_count"] = 8
        validate_apps_dict["app1"]["grant_table_count"] = 22
        validate_apps_dict["app1"]["token_table_count"] = 22

        validate_apps_dict["app3"]["synth_bene_cnt"] = 6
        validate_apps_dict["app3"]["grant_synthetic_bene_count"] = 6
        validate_apps_dict["app3"][
            "grant_and_archived_synthetic_bene_deduped_count"
        ] = 6
        validate_apps_dict["app3"]["token_synthetic_bene_count"] = 6
        validate_apps_dict["app3"]["grant_table_count"] = 17
        validate_apps_dict["app3"]["token_table_count"] = 17

        self._validate_global_state_per_app_metrics_log(validate_apps_dict)

        """
        TEST #6:

        Test that missing/NULL crosswalk record is not counted.

        Removing one real bene crosswalk should reduce real counts by 1.
        """
        # Removing one real bene crosswalk
        cw = Crosswalk.objects.get(user=save_real_user_dict["60000000000001"])
        cw.delete()

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "real_bene_cnt": 20,  # 21 -> 20
            "crosswalk_real_bene_count": 20,  # 21 -> 20
            "crosswalk_table_count": 38,  # 39 -> 38
            "grant_real_bene_count": 33,  # 36 -> 33
            "grant_real_bene_deduped_count": 15,  # 16 -> 15
            "grant_and_archived_real_bene_deduped_count": 17,  # 18 -> 17
            "token_real_bene_deduped_count": 15,  # 16 -> 15
            "token_real_bene_app_pair_deduped_count": 33,  # 36 -> 33
            "global_beneficiary_real_count": 20,  # 21 -> 20
            "global_beneficiary_real_grant_count": 15,  # 16 -> 15
            "global_beneficiary_real_grant_or_archived_count": 17,  # 18 -> 17
            "global_beneficiary_real_grant_not_archived_count": 15,  # 16 -> 15
            "global_beneficiary_real_token_count": 15,  # 16 -> 15
            "global_beneficiary_real_token_or_archived_count": 17,  # 18 -> 17
            "global_beneficiary_real_token_not_archived_count": 15,  # 16 -> 15
            "global_beneficiary_real_grant_to_apps_eq_3_count": 9,  # 10 -> 9
            "global_beneficiary_app_pair_real_grant_count": 33,  # 36 -> 33
            "global_beneficiary_app_pair_real_grant_vs_archived_difference_total_count": 33,  # 36 -> 33
        })
        self._validate_global_state_metrics_log(validate_global_dict)

        # Validate per app count changes
        validate_apps_dict["app0"]["real_bene_cnt"] = 12
        validate_apps_dict["app0"]["grant_real_bene_count"] = 12
        validate_apps_dict["app0"]["grant_and_archived_real_bene_deduped_count"] = 12
        validate_apps_dict["app0"]["token_real_bene_count"] = 12
        validate_apps_dict["app0"]["grant_table_count"] = 22
        validate_apps_dict["app0"]["token_table_count"] = 22

        validate_apps_dict["app1"]["real_bene_cnt"] = 12
        validate_apps_dict["app1"]["grant_real_bene_count"] = 12
        validate_apps_dict["app1"]["grant_and_archived_real_bene_deduped_count"] = 14
        validate_apps_dict["app1"]["token_real_bene_count"] = 12
        validate_apps_dict["app1"]["grant_table_count"] = 22
        validate_apps_dict["app1"]["token_table_count"] = 22

        validate_apps_dict["app3"]["real_bene_cnt"] = 9
        validate_apps_dict["app3"]["grant_real_bene_count"] = 9
        validate_apps_dict["app3"]["grant_and_archived_real_bene_deduped_count"] = 9
        validate_apps_dict["app3"]["token_real_bene_count"] = 9
        validate_apps_dict["app3"]["grant_table_count"] = 17
        validate_apps_dict["app3"]["token_table_count"] = 17

        self._validate_global_state_per_app_metrics_log(validate_apps_dict)

        """
        TEST #7:

        Tests for addition of global_developer_* counts per BB2-944
        """
        # Test 7A: Test changing from 4 to 2 distinct organizations.
        self._create_or_update_development_user(username="user_app0", organization="org one")
        self._create_or_update_development_user(username="user_app1", organization="org one")
        self._create_or_update_development_user(username="user_app2", organization="org two")
        self._create_or_update_development_user(username="user_app3", organization="org two")

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "global_developer_distinct_organization_name_count": 2,
        })
        self._validate_global_state_metrics_log(validate_global_dict)

        # Test 7B: Test changing from 0 to 2 apps with a first api call
        app = Application.objects.get(name="app0")
        app.first_active = timezone.now()
        app.save()
        app = Application.objects.get(name="app2")
        app.first_active = timezone.now()
        app.save()

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "global_developer_with_first_api_call_count": 2,
        })
        self._validate_global_state_metrics_log(validate_global_dict)

        # Test 7C: Test adding 3 development users to another org that do name have an application yet.
        self._create_or_update_development_user(username="user_no_app0", organization="org three")
        self._create_or_update_development_user(username="user_no_app1", organization="org three")
        self._create_or_update_development_user(username="user_no_app2", organization="org three")

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "global_developer_count": 7,
            "global_developer_distinct_organization_name_count": 3,
        })
        self._validate_global_state_metrics_log(validate_global_dict)

        """
        TEST #8:

        Tests for addition of global_beneficiary_* counts per BB2-944
        """
        """
          Test #8A:

          Create overlapping real & synth benes to validate global_beneficiary_*_grant_to_apps_*_count
        """
        # Create 3x real benes granted to 2x apps for: global_beneficiary_real_grant_to_apps_eq_2_count = 3
        for app_num in range(10, 12):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="7100000000000", count=3, app_name="app{}".format(str(app_num)),
                app_user_organization="app{}-org".format(str(app_num))
            )
        # Create 5x synth benes granted to 2x apps for: global_beneficiary_synthetic_grant_to_apps_eq_2_count = 5
        for app_num in range(10, 12):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="-7100000000000", count=5, app_name="app{}".format(str(app_num)),
                app_user_organization="app{}-org".format(str(app_num))
            )

        # Create 4x real benes granted to 4x apps for: global_beneficiary_real_grant_to_apps_eq_4thru5_count = 4
        for app_num in range(10, 14):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="7200000000000", count=4, app_name="app{}".format(str(app_num)),
                app_user_organization="app{}-org".format(str(app_num))
            )
        # Create 6x synth benes granted to 5x apps for: global_beneficiary_synthetic_grant_to_apps_eq_4thru5_count = 6
        for app_num in range(10, 15):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="-7200000000000", count=6, app_name="app{}".format(str(app_num)),
                app_user_organization="app" + str(app_num) + "-org"
            )

        # Create 3x real benes granted to 6x apps for: global_beneficiary_real_grant_to_apps_eq_6thru8_count = 3
        for app_num in range(10, 16):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="7300000000000", count=3, app_name="app{}".format(str(app_num)),
                app_user_organization="app{}-org".format(str(app_num))
            )
        # Create 2x synth benes granted to 8x apps for: global_beneficiary_synthetic_grant_to_apps_eq_6thru8_count = 2
        for app_num in range(10, 18):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="-7300000000000", count=2, app_name="app{}".format(str(app_num)),
                app_user_organization="app" + str(app_num) + "-org"
            )

        # Create 2x real benes granted to 9x apps for: global_beneficiary_real_grant_to_apps_eq_9thru13_count = 2
        for app_num in range(10, 19):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="7400000000000", count=2, app_name="app{}".format(str(app_num)),
                app_user_organization="app{}-org".format(str(app_num))
            )
        # Create 3x synth benes granted to 13x apps for: global_beneficiary_synthetic_grant_to_apps_eq_9thru13_count = 3
        for app_num in range(10, 23):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="-7400000000000", count=3, app_name="app{}".format(str(app_num)),
                app_user_organization="app" + str(app_num) + "-org"
            )

        # Create 1x real benes granted to 14x apps for: global_beneficiary_real_grant_to_apps_gt_13_count = 1
        for app_num in range(10, 24):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="7500000000000", count=1, app_name="app{}".format(str(app_num)),
                app_user_organization="app{}-org".format(str(app_num))
            )
        # Create 1x synth benes granted to 15x apps for: global_beneficiary_synthetic_grant_to_apps_gt_13_count = 1
        for app_num in range(10, 25):
            app, user_dict = self._create_range_users_app_token_grant(
                start_fhir_id="-7500000000000", count=1, app_name="app{}".format(str(app_num)),
                app_user_organization="app" + str(app_num) + "-org"
            )

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "real_bene_cnt": 33,  # 20 -> 33
            "synth_bene_cnt": 34,  # 17 -> 34
            "crosswalk_real_bene_count": 33,  # 20 -> 33
            "crosswalk_synthetic_bene_count": 34,  # 17 -> 34
            "crosswalk_table_count": 68,  # 38 -> 68
            "grant_real_bene_count": 105,  # 33 -> 105
            "grant_synthetic_bene_count": 134,  # 24 -> 134
            "grant_table_count": 245,  # 63 -> 245
            "grant_real_bene_deduped_count": 28,  # 15 -> 28
            "grant_synthetic_bene_deduped_count": 29,  # 12 -> 29
            "grant_and_archived_real_bene_deduped_count": 30,  # 17 -> 30
            "grant_and_archived_synthetic_bene_deduped_count": 32,  # 15 -> 32
            "token_real_bene_deduped_count": 28,  # 15 -> 28
            "token_synthetic_bene_deduped_count": 29,  # 12 -> 29
            "token_table_count": 245,  # 63 -> 245
            "token_real_bene_app_pair_deduped_count": 105,  # 33 -> 105
            "token_synthetic_bene_app_pair_deduped_count": 134,  # 24 -> 134
            "global_apps_active_cnt": 18,  # 3 -> 18
            "global_apps_require_demographic_scopes_cnt": 18,  # 3 -> 18
            "global_developer_count": 22,  # 7 -> 22
            "global_developer_with_registered_app_count": 19,  # 4 -> 19
            "global_developer_distinct_organization_name_count": 18,  # 3 -> 18
            "global_beneficiary_count": 69,  # 39 -> 69
            "global_beneficiary_real_count": 33,  # 20 -> 33
            "global_beneficiary_synthetic_count": 34,  # 17 -> 34
            "global_beneficiary_grant_count": 59,  # 29 -> 59
            "global_beneficiary_real_grant_count": 28,  # 15 -> 28
            "global_beneficiary_synthetic_grant_count": 29,  # 12 -> 29
            "global_beneficiary_grant_or_archived_count": 64,  # 34 -> 64
            "global_beneficiary_real_grant_or_archived_count": 30,  # 17 -> 30
            "global_beneficiary_synthetic_grant_or_archived_count": 32,  # 15 -> 32
            "global_beneficiary_grant_not_archived_count": 59,  # 29 -> 59
            "global_beneficiary_real_grant_not_archived_count": 28,  # 15 -> 28
            "global_beneficiary_synthetic_grant_not_archived_count": 29,  # 12 -> 29
            "global_beneficiary_real_grant_to_apps_eq_2_count": 3,  # 0 -> 3
            "global_beneficiary_synthetic_grant_to_apps_eq_2_count": 5,  # 0 -> 5
            "global_beneficiary_real_grant_to_apps_eq_4thru5_count": 4,  # 0 -> 4
            "global_beneficiary_synthetic_grant_to_apps_eq_4thru5_count": 6,  # 0 -> 6
            "global_beneficiary_real_grant_to_apps_eq_6thru8_count": 3,  # 0 -> 3
            "global_beneficiary_synthetic_grant_to_apps_eq_6thru8_count": 2,  # 0 -> 2
            "global_beneficiary_real_grant_to_apps_eq_9thru13_count": 2,  # 0 -> 2
            "global_beneficiary_synthetic_grant_to_apps_eq_9thru13_count": 3,  # 0 -> 3
            "global_beneficiary_real_grant_to_apps_gt_13_count": 1,  # 0 -> 1
            "global_beneficiary_synthetic_grant_to_apps_gt_13_count": 1,  # 0 -> 1
            "global_beneficiary_app_pair_grant_count": 245,  # 63 -> 245
            "global_beneficiary_app_pair_real_grant_count": 105,  # 33 -> 105
            "global_beneficiary_app_pair_synthetic_grant_count": 134,  # 24 -> 134
            "global_beneficiary_app_pair_grant_vs_archived_difference_total_count": 245,  # 63 -> 245
            "global_beneficiary_app_pair_real_grant_vs_archived_difference_total_count": 105,  # 33 -> 105
            "global_beneficiary_app_pair_synthetic_grant_vs_archived_difference_total_count": 134,  # 24 -> 134
        })
        self._validate_global_state_metrics_log(validate_global_dict)

        """
          Test #8B:

          Revoke grants created in test #8A to validate global_beneficiary_*_grant_archived_to_apps_*_count
        """
        # REVOKE 3x real benes granted to 2x apps for: global_beneficiary_real_grant_to_apps_eq_2_count = 3
        for app_num in range(10, 12):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="7100000000000", count=3, app_name="app{}".format(str(app_num))
            )
        # Revoke 5x synth benes granted to 2x apps for: global_beneficiary_synthetic_grant_to_apps_eq_2_count = 5
        for app_num in range(10, 12):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="-7100000000000", count=5, app_name="app{}".format(str(app_num))
            )

        # Revoke 4x real benes granted to 4x apps for: global_beneficiary_real_grant_to_apps_eq_4thru5_count = 4
        for app_num in range(10, 14):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="7200000000000", count=4, app_name="app{}".format(str(app_num))
            )
        # Revoke 6x synth benes granted to 5x apps for: global_beneficiary_synthetic_grant_to_apps_eq_4thru5_count = 6
        for app_num in range(10, 15):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="-7200000000000", count=6, app_name="app{}".format(str(app_num))
            )

        # Create 3x real benes granted to 6x apps for: global_beneficiary_real_grant_to_apps_eq_6thru8_count = 3
        for app_num in range(10, 16):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="7300000000000", count=3, app_name="app{}".format(str(app_num))
            )
        # Create 2x synth benes granted to 8x apps for: global_beneficiary_synthetic_grant_to_apps_eq_6thru8_count = 2
        for app_num in range(10, 18):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="-7300000000000", count=2, app_name="app{}".format(str(app_num))
            )

        # Create 2x real benes granted to 9x apps for: global_beneficiary_real_grant_to_apps_eq_9thru13_count = 2
        for app_num in range(10, 19):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="7400000000000", count=2, app_name="app{}".format(str(app_num))
            )
        # Create 3x synth benes granted to 13x apps for: global_beneficiary_synthetic_grant_to_apps_eq_9thru13_count = 3
        for app_num in range(10, 23):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="-7400000000000", count=3, app_name="app{}".format(str(app_num))
            )

        # Create 1x real benes granted to 14x apps for: global_beneficiary_real_grant_to_apps_gt_13_count = 1
        for app_num in range(10, 24):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="7500000000000", count=1, app_name="app{}".format(str(app_num))
            )
        # Create 1x synth benes granted to 15x apps for: global_beneficiary_synthetic_grant_to_apps_gt_13_count = 1
        for app_num in range(10, 25):
            self._revoke_range_users_app_token_grant(
                start_fhir_id="-7500000000000", count=1, app_name="app{}".format(str(app_num))
            )

        self._call_management_command_log_global_state_metrics()

        # Update with metrics changes.
        validate_global_dict.update({
            "grant_real_bene_count": 33,  # 105 -> 33
            "grant_synthetic_bene_count": 24,  # 134 -> 24
            "grant_table_count": 63,  # 245 -> 63
            "grant_archived_table_count": 187,  # 5 -> 187
            "grant_real_bene_deduped_count": 15,  # 28 -> 15
            "grant_synthetic_bene_deduped_count": 12,  # 29 -> 12
            "grantarchived_real_bene_deduped_count": 15,  # 2 -> 15
            "grantarchived_synthetic_bene_deduped_count": 20,  # 3 -> 20
            "token_real_bene_deduped_count": 15,  # 28 -> 15
            "token_synthetic_bene_deduped_count": 12,  # 29 -> 12
            "token_table_count": 63,  # 245 -> 63
            "token_archived_table_count": 187,  # 5 -> 187
            "token_real_bene_app_pair_deduped_count": 33,  # 105 -> 33
            "token_synthetic_bene_app_pair_deduped_count": 24,  # 134 -> 24
            "global_beneficiary_grant_count": 29,  # 59 -> 29
            "global_beneficiary_real_grant_count": 15,  # 28 -> 15
            "global_beneficiary_synthetic_grant_count": 12,  # 29 -> 12
            "global_beneficiary_grant_archived_count": 35,  # 5 -> 35
            "global_beneficiary_real_grant_archived_count": 15,  # 2 -> 15
            "global_beneficiary_synthetic_grant_archived_count": 20,  # 3 -> 20
            "global_beneficiary_grant_not_archived_count": 29,  # 59 -> 29
            "global_beneficiary_real_grant_not_archived_count": 15,  # 28 -> 15
            "global_beneficiary_synthetic_grant_not_archived_count": 12,  # 29 -> 12
            "global_beneficiary_archived_not_grant_count": 35,  # 5 -> 35
            "global_beneficiary_real_archived_not_grant_count": 15,  # 2 -> 15
            "global_beneficiary_synthetic_archived_not_grant_count": 20,  # 3 -> 20
            "global_beneficiary_real_grant_to_apps_eq_2_count": 0,  # 3 -> 0
            "global_beneficiary_synthetic_grant_to_apps_eq_2_count": 0,  # 5 -> 0
            "global_beneficiary_real_grant_to_apps_eq_4thru5_count": 0,  # 4 -> 0
            "global_beneficiary_synthetic_grant_to_apps_eq_4thru5_count": 0,  # 6 -> 0
            "global_beneficiary_real_grant_to_apps_eq_6thru8_count": 0,  # 3 -> 0
            "global_beneficiary_synthetic_grant_to_apps_eq_6thru8_count": 0,  # 2 -> 0
            "global_beneficiary_real_grant_to_apps_eq_9thru13_count": 0,  # 2 -> 0
            "global_beneficiary_synthetic_grant_to_apps_eq_9thru13_count": 0,  # 3 -> 0
            "global_beneficiary_real_grant_to_apps_gt_13_count": 0,  # 1 -> 0
            "global_beneficiary_synthetic_grant_to_apps_gt_13_count": 0,  # 1 -> 0
            "global_beneficiary_real_grant_archived_to_apps_eq_2_count": 3,  # 0 -> 3
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_2_count": 5,  # 0 -> 5
            "global_beneficiary_real_grant_archived_to_apps_eq_4thru5_count": 4,  # 0 -> 4
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_4thru5_count": 6,  # 0 -> 6
            "global_beneficiary_real_grant_archived_to_apps_eq_6thru8_count": 3,  # 0 -> 3
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_6thru8_count": 2,  # 0 -> 2
            "global_beneficiary_real_grant_archived_to_apps_eq_9thru13_count": 2,  # 0 -> 2
            "global_beneficiary_synthetic_grant_archived_to_apps_eq_9thru13_count": 3,  # 0 -> 3
            "global_beneficiary_real_grant_archived_to_apps_gt_13_count": 1,  # 0 -> 1
            "global_beneficiary_synthetic_grant_archived_to_apps_gt_13_count": 1,  # 0 -> 1
            "global_beneficiary_app_pair_grant_count": 63,  # 245 -> 63
            "global_beneficiary_app_pair_real_grant_count": 33,  # 105 -> 33
            "global_beneficiary_app_pair_synthetic_grant_count": 24,  # 134 -> 24
            "global_beneficiary_app_pair_grant_archived_count": 187,  # 5 -> 187
            "global_beneficiary_app_pair_real_grant_archived_count": 74,  # 2 -> 74
            "global_beneficiary_app_pair_synthetic_grant_archived_count": 113,  # 3 -> 113
            "global_beneficiary_app_pair_grant_vs_archived_difference_total_count": 63,  # 245 -> 63
            "global_beneficiary_app_pair_real_grant_vs_archived_difference_total_count": 33,  # 105 -> 33
            "global_beneficiary_app_pair_synthetic_grant_vs_archived_difference_total_count": 24,  # 134 -> 24
            "global_beneficiary_app_pair_archived_vs_grant_difference_total_count": 187,  # 5 -> 187
            "global_beneficiary_app_pair_real_archived_vs_grant_difference_total_count": 74,  # 2 -> 74
            "global_beneficiary_app_pair_synthetic_archived_vs_grant_difference_total_count": 113,  # 3 -> 113
        })
        self._validate_global_state_metrics_log(validate_global_dict)
