import json
import pytz
from datetime import datetime
from django.conf import settings
from django.test.client import Client
from httmock import HTTMock, urlmatch
from waffle import switch_is_active
from waffle.testutils import override_switch

from apps.test import BaseApiTest
from apps.authorization.models import (
    DataAccessGrant,
)
from apps.fhir.bluebutton.tests.test_fhir_resources_read_search_w_validation import (
    get_response_json,
)


class TestDataAccessGrantPermissions(BaseApiTest):
    APPLICATION_SCOPES_FULL = [
        "patient/Patient.read",
        "profile",
        "patient/ExplanationOfBenefit.read",
        "patient/Coverage.read",
    ]

    """
    Setup mocks for back-end server FHIR end point responses.
    """
    MOCK_FHIR_URL = "fhir.backend.bluebutton.hhsdevcloud.us"
    MOCK_FHIR_PATIENT_READVIEW_PATH_V1 = r"/v1/fhir/Patient/[-]?\d+[/]?"
    MOCK_FHIR_PATIENT_READVIEW_PATH_V2 = r"/v2/fhir/Patient/[-]?\d+[/]?"
    MOCK_FHIR_PATIENT_SEARCHVIEW_PATH_V1 = r"/v1/fhir/Patient[/]?"
    MOCK_FHIR_PATIENT_SEARCHVIEW_PATH_V2 = r"/v2/fhir/Patient[/]?"
    MOCK_FHIR_COVERAGE_READVIEW_PATH_V1 = r"/v1/fhir/Coverage/[-]?\d+[/]?"
    MOCK_FHIR_COVERAGE_READVIEW_PATH_V2 = r"/v2/fhir/Coverage/[-]?\d+[/]?"
    MOCK_FHIR_COVERAGE_SEARCHVIEW_PATH_V1 = r"/v1/fhir/Coverage[/]?"
    MOCK_FHIR_COVERAGE_SEARCHVIEW_PATH_V2 = r"/v2/fhir/Coverage[/]?"
    MOCK_FHIR_EOB_READVIEW_PATH_V1 = r"/v1/fhir/ExplanationOfBenefit/[-]?\d+[/]?"
    MOCK_FHIR_EOB_READVIEW_PATH_V2 = r"/v2/fhir/ExplanationOfBenefit/[-]?\d+[/]?"
    MOCK_FHIR_EOB_SEARCHVIEW_PATH_V1 = r"/v1/fhir/ExplanationOfBenefit[/]?"
    MOCK_FHIR_EOB_SEARCHVIEW_PATH_V2 = r"/v2/fhir/ExplanationOfBenefit[/]?"

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_PATIENT_READVIEW_PATH_V1)
    def fhir_request_patient_readview_v1_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("patient_read_v1")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_PATIENT_READVIEW_PATH_V2)
    def fhir_request_patient_readview_v2_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("patient_read_v2")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_PATIENT_SEARCHVIEW_PATH_V1)
    def fhir_request_patient_searchview_v1_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("patient_search_v1")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_PATIENT_SEARCHVIEW_PATH_V2)
    def fhir_request_patient_searchview_v2_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("patient_search_v2")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_COVERAGE_READVIEW_PATH_V1)
    def fhir_request_coverage_readview_v1_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("coverage_read_v1")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_COVERAGE_READVIEW_PATH_V2)
    def fhir_request_coverage_readview_v2_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("coverage_read_v2")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_COVERAGE_SEARCHVIEW_PATH_V1)
    def fhir_request_coverage_searchview_v1_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("coverage_search_v1")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_COVERAGE_SEARCHVIEW_PATH_V2)
    def fhir_request_coverage_searchview_v2_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("coverage_search_v2")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_EOB_READVIEW_PATH_V1)
    def fhir_request_eob_readview_v1_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("eob_read_in_pt_v1")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_EOB_READVIEW_PATH_V2)
    def fhir_request_eob_readview_v2_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("eob_read_in_pt_v2")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_EOB_SEARCHVIEW_PATH_V1)
    def fhir_request_eob_searchview_v1_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("eob_search_v1")}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_EOB_SEARCHVIEW_PATH_V2)
    def fhir_request_eob_searchview_v2_success_mock(self, url, request):
        return {"status_code": 200, "content": get_response_json("eob_search_v2")}

    def setUp(self):
        # create read and write capabilities
        self.read_capability = self._create_capability("Read", [])
        self.write_capability = self._create_capability("Write", [])
        self.patient_capability = self._create_capability(
            "patient",
            [
                ["GET", r"\/v[1,2]\/fhir\/Patient\/\-\d+"],
                ["GET", r"\/v[1,2]\/fhir\/Patient\/\d+"],
                ["GET", r"/v[1,2]/fhir/Patient"],
            ],
        )
        self._create_capability(
            "coverage",
            [
                ["GET", r"\/v[1,2]\/fhir\/Coverage\/.+"],
                ["GET", r"/v[1,2]/fhir/Coverage"],
            ],
        )
        self._create_capability(
            "eob",
            [
                ["GET", r"\/v[1,2]\/fhir\/ExplanationOfBenefit\/.+"],
                ["GET", r"/v[1,2]/fhir/ExplanationOfBenefit"],
            ],
        )
        # Setup the RequestFactory
        self.client = Client()

    def _assert_call_all_fhir_endpoints(self, access_token=None,
                                        expected_response_code=None,
                                        expected_response_detail_mesg=None):
        """
        This method calls all FHIR and Profile (userinfo)
        end points for use in tests.

        The asserts will check for the expected_response_code
        and expected_response_detail_mesg to match.
        """
        # Test profile/userinfo v1
        response = self.client.get(
            "/v1/connect/userinfo", HTTP_AUTHORIZATION="Bearer " + access_token
        )
        self.assertEqual(response.status_code, expected_response_code)
        if expected_response_detail_mesg is not None:
            content = json.loads(response.content)
            self.assertEqual(content["detail"], expected_response_detail_mesg)

        # Test profile/userinfo v2
        response = self.client.get(
            "/v2/connect/userinfo", HTTP_AUTHORIZATION="Bearer " + access_token
        )
        self.assertEqual(response.status_code, expected_response_code)
        if expected_response_detail_mesg is not None:
            content = json.loads(response.content)
            self.assertEqual(content["detail"], expected_response_detail_mesg)

        # Test FHIR read views
        with HTTMock(
            self.fhir_request_patient_readview_v1_success_mock,
            self.fhir_request_coverage_readview_v1_success_mock,
            self.fhir_request_eob_readview_v1_success_mock,
            self.fhir_request_patient_readview_v2_success_mock,
            self.fhir_request_coverage_readview_v2_success_mock,
            self.fhir_request_eob_readview_v2_success_mock,
        ):
            for path in [
                "/v1/fhir/Patient/-20140000008325",
                "/v1/fhir/Coverage/-20140000008325",
                "/v1/fhir/ExplanationOfBenefit/-20140000008325"
                "/v2/fhir/Patient/-20140000008325",
                "/v2/fhir/Coverage/-20140000008325",
                "/v2/fhir/ExplanationOfBenefit/-20140000008325",
            ]:
                response = self.client.get(
                    path, HTTP_AUTHORIZATION="Bearer " + access_token
                )
                self.assertEqual(response.status_code, expected_response_code)
                if expected_response_detail_mesg is not None:
                    content = json.loads(response.content)
                    self.assertEqual(content["detail"], expected_response_detail_mesg)

        # Test FHIR search views
        with HTTMock(
            self.fhir_request_patient_searchview_v1_success_mock,
            self.fhir_request_coverage_searchview_v1_success_mock,
            self.fhir_request_eob_searchview_v1_success_mock,
            self.fhir_request_patient_searchview_v2_success_mock,
            self.fhir_request_coverage_searchview_v2_success_mock,
            self.fhir_request_eob_searchview_v2_success_mock,
        ):
            for path in [
                "/v1/fhir/Patient?patient=-20140000008325",
                "/v1/fhir/Coverage?patient=-20140000008325",
                "/v1/fhir/Patient",
                "/v2/fhir/Patient?patient=-20140000008325",
                "/v2/fhir/Coverage?patient=-20140000008325",
                "/v2/fhir/Patient",
            ]:
                response = self.client.get(
                    path, HTTP_AUTHORIZATION="Bearer " + access_token
                )
                self.assertEqual(response.status_code, expected_response_code)
                if expected_response_detail_mesg is not None:
                    content = json.loads(response.content)
                    self.assertEqual(content["detail"], expected_response_detail_mesg)

    @override_switch('limit_data_access', active=False)
    def test_research_study_app_type_without_switch_limit_data_access(self):
        """
        Test data access for FHIR and profile end points
        with limit-data-access switch False.
        """
        assert not switch_is_active('limit_data_access')

        # 1. Use helper method to create app, user, authorized grant & access token.
        user, app, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id="-20140000008325",
            app_name="test_app1",
            app_username="devuser1",
            app_user_organization="org1",
        )

        #     Test grant exists.
        self.assertTrue(
            DataAccessGrant.objects.filter(
                beneficiary=user,
                application=app,
            ).exists()
        )

        # 2. Test that all calls are successful (response_code=200)
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200
        )

        # 3. Test with application in-active/disabled (response_code=403)
        app.active = False
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=403,
            expected_response_detail_mesg=settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name)
        )

        # 4. Test with RESEARCH_STUDY application end_date IS NOT expired (response_code=200)
        app.active = True
        app.data_access_type = "RESEARCH_STUDY"
        app.end_date = datetime(2199, 1, 15, 0, 0, 0, 0, pytz.UTC)
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200
        )

        # 5. Test with RESEARCH_STUDY application end_date IS expired w/o feature switch (response_code=200)
        app.active = True
        app.data_access_type = "RESEARCH_STUDY"
        app.end_date = datetime(1999, 1, 15, 0, 0, 0, 0, pytz.UTC)
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200)

        # 3. Test that all calls return 401 (Unauthorized) after grant delete
        dag = DataAccessGrant.objects.get(
            beneficiary__username="firstlast1@example.com",
            application__name="test_app1",
        )
        dag.delete()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"],
            expected_response_code=401,
            expected_response_detail_mesg="Authentication credentials were not provided."
        )

    @override_switch('limit_data_access', active=True)
    def test_research_study_app_type_with_switch_limit_data_access(self):
        """
        Test data access for FHIR and profile end points
        with limit-data-access switch True.
        """
        assert switch_is_active('limit_data_access')

        # 1. Use helper method to create app, user, authorized grant & access token.
        user, app, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id="-20140000008325",
            app_name="test_app1",
            app_username="devuser1",
            app_user_organization="org1",
        )

        #     Test grant exists.
        self.assertTrue(
            DataAccessGrant.objects.filter(
                beneficiary=user,
                application=app,
            ).exists()
        )

        # 2. Test that all calls are successful (response_code=200)
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200
        )

        # 3. Test with application in-active/disabled (response_code=403)
        app.active = False
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=403,
            expected_response_detail_mesg=settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name)
        )

        # 4. Test with RESEARCH_STUDY application end_date IS NOT expired (response_code=200)
        app.active = True
        app.data_access_type = "RESEARCH_STUDY"
        app.end_date = datetime(2199, 1, 15, 0, 0, 0, 0, pytz.UTC)
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200
        )

        # 5. Test with RESEARCH_STUDY application end_date IS expired (response_code=401)
        app.active = True
        app.data_access_type = "RESEARCH_STUDY"
        app.end_date = datetime(1999, 1, 15, 0, 0, 0, 0, pytz.UTC)
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=401,
            expected_response_detail_mesg=settings.APPLICATION_RESEARCH_STUDY_ENDED_MESG
        )
