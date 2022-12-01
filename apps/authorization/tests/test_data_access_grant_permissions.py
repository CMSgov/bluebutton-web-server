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


class TestDataAccessPermissions(BaseApiTest):
    """
    Provides data access tests related to the
    following settings:

      - Application.data_access_type
      - Application.end_date
      - DataAcessGrant.expiration_date

    Tests are performed against API end points for:

      - FHIR read/searc resources
      - OAuth 2.0 auth end points
    """
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

    def _assert_call_token_refresh_endpoint(self, application=None,
                                            refresh_token=None,
                                            expected_response_code=None,
                                            expected_response_error_mesg=None,
                                            expected_response_error_description_mesg=None):
        """
        This method calls the token refresh end point
        for use in tests.

        The asserts will check for the expected_response_code,
        expected_response_error_mesg and expected_response_error_description_mesg to match.
        """
        refresh_post_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            "redirect_uri": application.redirect_uris,
            'client_id': application.client_id,
            'client_secret': application.client_secret,
        }
        response = self.client.post("/v1/o/token/", data=refresh_post_data)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, expected_response_code)
        if expected_response_error_mesg is not None:
            self.assertEqual(content["error"], expected_response_error_mesg)
        if expected_response_error_description_mesg is not None:
            self.assertEqual(content["error_description"], expected_response_error_description_mesg)
        return content

    @override_switch('limit_data_access', active=False)
    def test_research_study_app_type_without_switch_limit_data_access(self):
        """
        Test Application.data_access_type="RESEARCH_STUDY".

        Test data access for FHIR and profile end points
        with limit_data_access switch False.
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
            app_data_access_type="RESEARCH_STUDY",
            app_end_date=datetime(2199, 1, 15, 0, 0, 0, 0, pytz.UTC)
        )
        self.assertEqual(app.data_access_type, "RESEARCH_STUDY")
        self.assertEqual(app.end_date, datetime(2199, 1, 15, 0, 0, 0, 0, pytz.UTC))

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

        # 3. Test token refresh is successful (response_code=200)
        ac = self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=200
        )

        # 4. Set application to in-active/disabled
        app.active = False
        app.save()

        # 5. Test FHIR end point while app in-active/disabled (response_code=401)
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=401,
            expected_response_detail_mesg=settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name)
        )

        # 6. Test token refresh after applciation in-active/disabled (response_code=401)
        self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=401,
            expected_response_error_mesg="invalid_client",
            expected_response_error_description_mesg=settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name)
        )

        # 7. Set application to active/endabled
        app.active = True
        app.save()

        # 8. Test with RESEARCH_STUDY application end_date IS NOT expired (response_code=200)
        app.end_date = datetime(2199, 1, 15, 0, 0, 0, 0, pytz.UTC)
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200
        )

        # 9. Test app not expired token refresh (response_code=200)
        ac = self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=200
        )

        # 10. Test with RESEARCH_STUDY application end_date IS expired w/o feature switch (response_code=200)
        app.data_access_type = "RESEARCH_STUDY"
        app.end_date = datetime(1999, 1, 15, 0, 0, 0, 0, pytz.UTC)
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200)

        # 11. Test app expired token refresh (response_code=200)
        ac = self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=200
        )

    @override_switch('limit_data_access', active=True)
    def test_research_study_app_type_with_switch_limit_data_access(self):
        """
        Test Application.data_access_type="RESEARCH_STUDY".

        Test data access for FHIR and profile end points
        with limit_data_access switch True.
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
            app_data_access_type="RESEARCH_STUDY",
            app_end_date=datetime(2199, 1, 15, 0, 0, 0, 0, pytz.UTC)
        )
        self.assertEqual(app.data_access_type, "RESEARCH_STUDY")
        self.assertEqual(app.end_date, datetime(2199, 1, 15, 0, 0, 0, 0, pytz.UTC))

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

        # 3. Test token refresh is successful (response_code=200)
        ac = self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=200
        )

        # 4. Set application to in-active/disabled
        app.active = False
        app.save()

        # 5. Test FHIR end point while app in-active/disabled (response_code=401)
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=401,
            expected_response_detail_mesg=settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name)
        )

        # 6. Test token refresh after applciation in-active/disabled (response_code=401)
        self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=401,
            expected_response_error_mesg="invalid_client",
            expected_response_error_description_mesg=settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name)
        )

        # 7. Set application to active/endabled
        app.active = True
        app.save()

        # 8. Test with RESEARCH_STUDY application end_date IS NOT expired (response_code=200)
        app.data_access_type = "RESEARCH_STUDY"
        app.end_date = datetime(2199, 1, 15, 0, 0, 0, 0, pytz.UTC)
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200
        )

        # 9. Test app not expired token refresh (response_code=200)
        ac = self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=200
        )

        # 10. Test with RESEARCH_STUDY application end_date IS expired (response_code=401)
        app.data_access_type = "RESEARCH_STUDY"
        app.end_date = datetime(1999, 1, 15, 0, 0, 0, 0, pytz.UTC)
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=401,
            expected_response_detail_mesg=settings.APPLICATION_RESEARCH_STUDY_ENDED_MESG
        )

        # 11. Test app expired token refresh (response_code=401)
        ac = self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=401,
            expected_response_error_mesg="invalid_client",
            expected_response_error_description_mesg=settings.APPLICATION_RESEARCH_STUDY_ENDED_MESG
        )

    @override_switch('limit_data_access', active=False)
    def test_one_time_app_type_without_switch_limit_data_access(self):
        """
        Test Application.data_access_type="ONE_TIME"
        with limit_data_access switch False.

        NOTE: This type of application does not allow token refreshes
              when the feature switch is enabled.
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
            app_data_access_type="ONE_TIME"
        )

        #     Test application default data access type
        self.assertEqual(app.data_access_type, "ONE_TIME")

        #     Test grant exists.
        self.assertTrue(
            DataAccessGrant.objects.filter(
                beneficiary=user,
                application=app,
            ).exists()
        )

        # 2. Test token refresh is working OK (response_code=200)
        ac = self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=200
        )

        # 3. Test that all calls are successful (response_code=200)
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200
        )

    @override_switch('limit_data_access', active=True)
    def test_one_time_app_type_with_switch_limit_data_access(self):
        """
        Test Application.data_access_type="ONE_TIME"
        with limit_data_access switch True

        NOTE: This type of application does not allow token refreshes
              when the feature switch is enabled.
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
            app_data_access_type="ONE_TIME"
        )

        #     Test application default data access type
        self.assertEqual(app.data_access_type, "ONE_TIME")

        #     Test grant exists.
        self.assertTrue(
            DataAccessGrant.objects.filter(
                beneficiary=user,
                application=app,
            ).exists()
        )

        # 2. Test token refresh is disabled for app (response_code=401)
        self._assert_call_token_refresh_endpoint(
            application=app, refresh_token=ac["refresh_token"], expected_response_code=401,
            expected_response_error_mesg="invalid_client",
            expected_response_error_description_mesg=settings.APPLICATION_ONE_TIME_REFRESH_NOT_ALLOWED_MESG
        )

        # 3. Test that all calls are successful (response_code=200)
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200
        )
