import json
import jsonschema

from django.core.management import call_command
from django.test.client import Client
from jsonschema import validate
from io import StringIO

from apps.test import BaseApiTest

from .audit_logger_schemas import GLOBAL_STATE_METRICS_LOG_SCHEMA, GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA


loggers = [
    'audit.global_state_metrics'
]


class TestLoggersGlobalMetricsManagementCommand(BaseApiTest):

    def setUp(self):
        # Setup the RequestFactory
        self.client = Client()
        self._redirect_loggers(loggers)

    def tearDown(self):
        self._cleanup_logger()

    def _get_log_content(self, logger_name):
        return self._collect_logs(loggers).get(logger_name)

    def _validateJsonSchema(self, schema, content):
        try:
            validate(instance=content, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            # Show error info for debugging
            print("jsonschema.exceptions.ValidationError: ", e)
            return False
        return True

    def test_management_command_logging(self):
        # Setup variety of real/synth users, apps and grants to test with using BaseApiTest helper function.
        for i in range(0, 3):
            user, app, ac = self._create_user_app_token_grant(first_name="real",
                                                              last_name="smith0" + str(i),
                                                              fhir_id="2000000000000" + str(i),
                                                              app_name="app0",
                                                              app_username="user_app0")
        for i in range(0, 2):
            user, app, ac = self._create_user_app_token_grant(first_name="synth",
                                                              last_name="smith0" + str(i),
                                                              fhir_id="-2000000000000" + str(i),
                                                              app_name="app0",
                                                              app_username="user_app0")
        for i in range(0, 2):
            user, app, ac = self._create_user_app_token_grant(first_name="real",
                                                              last_name="smith1" + str(i),
                                                              fhir_id="2000000000001" + str(i),
                                                              app_name="app1",
                                                              app_username="user_app1")
        for i in range(0, 3):
            user, app, ac = self._create_user_app_token_grant(first_name="synth",
                                                              last_name="smith1" + str(i),
                                                              fhir_id="-2000000000001" + str(i),
                                                              app_name="app1",
                                                              app_username="user_app1")
        for i in range(0, 5):
            user, app, ac = self._create_user_app_token_grant(first_name="real",
                                                              last_name="smith2" + str(i),
                                                              fhir_id="2000000000002" + str(i),
                                                              app_name="app2",
                                                              app_username="user_app2")
        app.require_demographic_scopes = False
        app.save()
        for i in range(0, 7):
            user, app, ac = self._create_user_app_token_grant(first_name="synth",
                                                              last_name="smith2" + str(i),
                                                              fhir_id="-2000000000002" + str(i),
                                                              app_name="app2",
                                                              app_username="user_app2")
        for i in range(0, 1):
            user, app, ac = self._create_user_app_token_grant(first_name="synth",
                                                              last_name="smith2" + str(i),
                                                              fhir_id="-2000000000003" + str(i),
                                                              app_name="app3",
                                                              app_username="user_app3")
        app.active = False
        app.save()

        # Call management command
        call_command("log_global_state_metrics", stdout=StringIO(), stderr=StringIO())

        # Get all log entries
        log_content = self._get_log_content('audit.global_state_metrics')
        self.assertIsNotNone(log_content)

        # Set buffer to read log lines from
        log_content_buf = StringIO(log_content)

        '''
        Validate 1st log line has:
            {'type': 'global_state_metrics',
              'group_timestamp': '2021-06-11T18:50:14+00:00',
              'real_bene_cnt': 10,
              'synth_bene_cnt': 12,
              'global_apps_active_cnt': 3,
              'global_apps_inactive_cnt': 1,
              'global_apps_require_demographic_scopes_cnt': 2}
        '''
        log_line = json.loads(log_content_buf.readline())
        self.assertTrue(self._validateJsonSchema(GLOBAL_STATE_METRICS_LOG_SCHEMA, log_line))

        # Per app expected value LISTs
        active_list = [True, True, True, False]
        require_demographic_scopes_list = [True, True, False, True]
        real_bene_cnt_list = [3, 2, 5, 0]
        synth_bene_cnt_list = [2, 3, 7, 1]

        # Validate per app log entries
        cnt = 0
        for log_line in log_content_buf.readlines():
            log_dict = json.loads(log_line)

            # Update Json Schema
            GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"]["name"]["pattern"] = "app{}".format(cnt)
            GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"]["active"]["enum"] = [active_list[cnt]]
            GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"]["require_demographic_scopes"]["enum"] = [
                require_demographic_scopes_list[cnt]
            ]
            GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"]["real_bene_cnt"]["enum"] = [real_bene_cnt_list[cnt]]
            GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA["properties"]["synth_bene_cnt"]["enum"] = [synth_bene_cnt_list[cnt]]

            # Validate with schema
            self.assertTrue(self._validateJsonSchema(GLOBAL_STATE_METRICS_PER_APP_LOG_SCHEMA, log_dict))
            cnt = cnt + 1
