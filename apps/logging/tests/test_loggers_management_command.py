import json
import jsonschema

from django.core.management import call_command
from django.test.client import Client
from jsonschema import validate
from io import StringIO

from apps.dot_ext.tests.test_models import TestDotExtModels
from apps.test import BaseApiTest

from .audit_logger_schemas import GLOBAL_STATE_METRICS_LOG_SCHEMA


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
        # Run test method from apps/dot_ext/tests/test_models.py to populate DB with applicaiton entries.
        TestDotExtModels().test_application_count_funcs()

        # Create 5x Real (positive FHIR_ID) users
        for cnt in range(5):
            self._create_user('johnsmith' + str(cnt), 'password',
                              first_name='John1' + str(cnt),
                              last_name='Smith',
                              email='john' + str(cnt) + '@smith.net',
                              fhir_id='2000000000000' + str(cnt),
                              user_hicn_hash='239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt),
                              user_mbi_hash='9876543217ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt))

        # Create 7x Synthetic (negative FHIR_ID) users and access tokens for application2
        for cnt in range(7):
            self._create_user('johndoe' + str(cnt), 'password',
                              first_name='John' + str(cnt),
                              last_name='Doe',
                              email='john' + str(cnt) + '@doe.net',
                              fhir_id='-2000000000000' + str(cnt),
                              user_hicn_hash='255e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt),
                              user_mbi_hash='987654321aaaa11111aaaa195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt))

        '''
        Call management command that produces the following entry to be validated with JsonSchema:

            {"type": "global_state_metrics", "group_timestamp": "2021-04-12T19:24:00+00:00",
             "real_bene_cnt": 5, "synth_bene_cnt": 7, "global_apps_active_cnt": 7,
             "global_apps_inactive_cnt": 3, "global_apps_require_demographic_scopes_cnt": 5}
        '''
        out = StringIO()
        call_command("log_global_state_metrics", stdout=out, stderr=StringIO())

        # Validate log entry
        log_content = self._get_log_content('audit.global_state_metrics')
        self.assertIsNotNone(log_content)
        log_content_dict = json.loads(log_content)
        self.assertTrue(self._validateJsonSchema(GLOBAL_STATE_METRICS_LOG_SCHEMA, log_content_dict))
