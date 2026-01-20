import json
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test.client import Client
from httmock import HTTMock, urlmatch
from oauth2_provider.models import get_access_token_model, get_refresh_token_model
from unittest import mock
from http import HTTPStatus

from apps.test import BaseApiTest
from apps.authorization.models import (
    DataAccessGrant,
)
from waffle.testutils import override_switch, override_flag
from apps.fhir.bluebutton.tests.test_fhir_resources_read_search_w_validation import (
    get_response_json,
)

from apps.versions import Versions
from hhs_oauth_server.settings.base import MOCK_FHIR_ENDPOINT_HOSTNAME

AccessToken = get_access_token_model()
RefreshToken = get_refresh_token_model()


class StubDate(datetime):
    pass


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
    MOCK_FHIR_URL = MOCK_FHIR_ENDPOINT_HOSTNAME  # "fhir.backend.bluebutton.hhsdevcloud.us"
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
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('patient_read_v1')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_PATIENT_READVIEW_PATH_V2)
    def fhir_request_patient_readview_v2_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('patient_read_v2')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_PATIENT_SEARCHVIEW_PATH_V1)
    def fhir_request_patient_searchview_v1_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('patient_search_v1')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_PATIENT_SEARCHVIEW_PATH_V2)
    def fhir_request_patient_searchview_v2_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('patient_search_v2')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_COVERAGE_READVIEW_PATH_V1)
    def fhir_request_coverage_readview_v1_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('coverage_read_v1')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_COVERAGE_READVIEW_PATH_V2)
    def fhir_request_coverage_readview_v2_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('coverage_read_v2')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_COVERAGE_SEARCHVIEW_PATH_V1)
    def fhir_request_coverage_searchview_v1_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('coverage_search_v1')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_COVERAGE_SEARCHVIEW_PATH_V2)
    def fhir_request_coverage_searchview_v2_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('coverage_search_v2')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_EOB_READVIEW_PATH_V1)
    def fhir_request_eob_readview_v1_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('eob_read_in_pt_v1')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_EOB_READVIEW_PATH_V2)
    def fhir_request_eob_readview_v2_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('eob_read_in_pt_v2')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_EOB_SEARCHVIEW_PATH_V1)
    def fhir_request_eob_searchview_v1_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('eob_search_v1')}

    @urlmatch(netloc=MOCK_FHIR_URL, path=MOCK_FHIR_EOB_SEARCHVIEW_PATH_V2)
    def fhir_request_eob_searchview_v2_success_mock(self, url, request):
        return {'status_code': HTTPStatus.OK, 'content': get_response_json('eob_search_v2')}

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

    @override_switch('v3_endpoints', active=True)
    @override_flag('v3_early_adopter', active=True)
    def _assert_call_all_fhir_endpoints(
        self,
        access_token=None,
        expected_response_code=None,
        expected_response_detail_mesg=None,
    ):
        """
        This method calls all FHIR and Profile/user_info
        end points for use in tests.

        The asserts will check for the expected_response_code
        and expected_response_detail_mesg to match.
        """
        try:
            ac = AccessToken.objects.get(token=access_token)
            ac.scope = 'patient/Coverage.read patient/Patient.read patient/ExplanationOfBenefit.read'
            ac.save()
        except Exception:
            pass

        # Test profile/userinfo v1
        response = self.client.get(
            "/v1/connect/userinfo", headers={"authorization": "Bearer " + access_token}
        )
        self.assertEqual(response.status_code, expected_response_code)
        if expected_response_detail_mesg is not None:
            content = json.loads(response.content)
            self.assertEqual(content["detail"], expected_response_detail_mesg)

        # Test profile/userinfo v2
        response = self.client.get(
            "/v2/connect/userinfo", headers={"authorization": "Bearer " + access_token}
        )
        self.assertEqual(response.status_code, expected_response_code)
        if expected_response_detail_mesg is not None:
            content = json.loads(response.content)
            self.assertEqual(content["detail"], expected_response_detail_mesg)

        # Test profile/userinfo v3
        response = self.client.get(
            "/v3/connect/userinfo", headers={"authorization": "Bearer " + access_token}
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
                "/v1/fhir/ExplanationOfBenefit/-20140000008325",
                "/v2/fhir/Patient/-20140000008325",
                "/v2/fhir/Coverage/-20140000008325",
                "/v2/fhir/ExplanationOfBenefit/-20140000008325",
            ]:
                response = self.client.get(
                    path, headers={"authorization": "Bearer " + access_token}
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
                "/v1/fhir/Patient?identifier=-20140000008325",
                "/v1/fhir/Coverage?beneficiary=-20140000008325",
                "/v1/fhir/Patient",
                "/v2/fhir/Patient?identifier=-20140000008325",
                "/v2/fhir/Coverage?beneficiary=-20140000008325",
                "/v2/fhir/Patient",
            ]:
                response = self.client.get(
                    path, headers={"authorization": "Bearer " + access_token}
                )
                self.assertEqual(response.status_code, expected_response_code)
                if expected_response_detail_mesg is not None:
                    content = json.loads(response.content)
                    self.assertEqual(content["detail"], expected_response_detail_mesg)

    def _assert_call_token_refresh_endpoint(
        self,
        application=None,
        refresh_token=None,
        expected_response_code=None,
        expected_response_error_mesg=None,
        expected_response_error_description_mesg=None,
    ):
        """
        This method calls the token refresh end point
        for use in tests.

        The asserts will check for the expected_response_code,
        expected_response_error_mesg and expected_response_error_description_mesg to match.
        """
        refresh_post_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "redirect_uri": application.redirect_uris,
            "client_id": application.client_id,
            "client_secret": application.client_secret_plain,
        }
        response = self.client.post(f'/v{Versions.V2}/o/token/', data=refresh_post_data)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, expected_response_code)
        if expected_response_error_mesg is not None:
            self.assertEqual(content["error"], expected_response_error_mesg)
        if expected_response_error_description_mesg is not None:
            self.assertEqual(
                content["error_description"], expected_response_error_description_mesg
            )
        return content

    def test_revoked_data_access_grant(self):
        """
        Test data access grant deleted / revoked

        Test data access for FHIR and profile end points.
        """
        # 1. Use helper method to create app, user, authorized grant & access token.
        user, app, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id_v2="-20140000008325",
            fhir_id_v3="-30140000008325",
            app_name="test_app1",
            app_username="devuser1",
            app_user_organization="org1",
            mbi=self._generate_random_mbi(),
            app_data_access_type="RESEARCH_STUDY",
        )

        # 2. Test application data access type
        self.assertEqual(app.data_access_type, "RESEARCH_STUDY")

        # 3. Test grant obj created OK.
        dag = DataAccessGrant.objects.get(beneficiary=user, application=app)
        #     Assert is not None
        self.assertNotEqual(dag, None)

        #     Assert expiration date has been set to None
        self.assertEqual(dag.expiration_date, None)

        # 4. Test token refresh is enabled for app
        ac = self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.OK,
        )

        # 5. Test access & refresh tokens exist
        self.assertTrue(AccessToken.objects.filter(token=ac["access_token"]).exists())
        self.assertTrue(RefreshToken.objects.filter(token=ac["refresh_token"]).exists())

        # 6. Test that all FHIR calls are successful
        self._assert_call_all_fhir_endpoints(
            access_token=ac['access_token'], expected_response_code=HTTPStatus.OK
        )

        # 7. Delete /revoke data access grant
        dag.delete()

        # 8. Test access and refresh tokens are removed
        #    per delete signal on DataAccessGrant
        self.assertFalse(AccessToken.objects.filter(token=ac["access_token"]).exists())
        #    Note: refresh token exists still? But doesn't work per #9
        self.assertTrue(RefreshToken.objects.filter(token=ac["refresh_token"]).exists())

        # 9. Test token refresh gets an invalid_grant response
        self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.FORBIDDEN,
            expected_response_error_mesg="invalid_grant",
        )
        # 10. Test that FHIR calls fail
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"],
            expected_response_code=HTTPStatus.UNAUTHORIZED,
            expected_response_detail_mesg="Authentication credentials were not provided.",
        )

    def test_research_study_app_type(self):
        """
        Test Application.data_access_type="RESEARCH_STUDY".

        Test data access for FHIR and profile end points
        """
        # 1. Use helper method to create app, user, authorized grant & access token.
        user, app, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id_v2="-20140000008325",
            fhir_id_v3="-30140000008325",
            app_name="test_app1",
            app_username="devuser1",
            app_user_organization="org1",
            mbi=self._generate_random_mbi(),
            app_data_access_type="RESEARCH_STUDY",
        )
        self.assertEqual(app.data_access_type, "RESEARCH_STUDY")

        #     Test grant exists.
        self.assertTrue(
            DataAccessGrant.objects.filter(
                beneficiary=user,
                application=app,
            ).exists()
        )

        # 2. Test that all calls are successful
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"], expected_response_code=200
        )

        # 3. Test token refresh is successful
        ac = self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.OK,
        )

        # 4. Set application to in-active/disabled
        app.active = False
        app.save()

        # 5. Test FHIR end point while app in-active/disabled
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"],
            expected_response_code=HTTPStatus.UNAUTHORIZED,
            expected_response_detail_mesg=settings.APPLICATION_TEMPORARILY_INACTIVE.format(
                app.name
            ),
        )

        # 6. Test token refresh after applciation in-active/disabled
        self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.FORBIDDEN,
            expected_response_error_mesg="invalid_client",
            expected_response_error_description_mesg=settings.APPLICATION_TEMPORARILY_INACTIVE.format(
                app.name
            ),
        )

        # 7. Set application to active/endabled
        app.active = True
        app.save()

        # 8. Re-test with RESEARCH_STUDY active
        app.data_access_type = "RESEARCH_STUDY"
        app.save()

        self._assert_call_all_fhir_endpoints(
            access_token=ac['access_token'], expected_response_code=HTTPStatus.OK
        )

        # 9. Test app not expired token refresh
        ac = self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.OK,
        )

    def test_one_time_app_type(self):
        """
        Test Application.data_access_type="ONE_TIME"

        NOTE: This type of application does not allow token refreshes
        """
        # 1. Use helper method to create app, user, authorized grant & access token.
        user, app, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id_v2="-20140000008325",
            fhir_id_v3="-30140000008325",
            app_name="test_app1",
            app_username="devuser1",
            app_user_organization="org1",
            mbi=self._generate_random_mbi(),
            app_data_access_type="ONE_TIME",
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

        # 2. Test token refresh is disabled for app
        self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.FORBIDDEN,
            expected_response_error_mesg="invalid_client",
            expected_response_error_description_mesg=settings.APPLICATION_ONE_TIME_REFRESH_NOT_ALLOWED_MESG,
        )

        # 3. Test that all calls are successful
        self._assert_call_all_fhir_endpoints(
            access_token=ac['access_token'], expected_response_code=HTTPStatus.OK
        )

    @mock.patch("apps.authorization.models.datetime", StubDate)
    def test_thirteen_month_app_type(self):
        """
        Test Application.data_access_type="THIRTEEN_MONTH"
        """
        # 1. Use helper method to create app, user, authorized grant & access token.
        user, app, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id_v2="-20140000008325",
            fhir_id_v3="-30140000008325",
            app_name="test_app1",
            app_username="devuser1",
            app_user_organization="org1",
            mbi=self._generate_random_mbi(),
            app_data_access_type="THIRTEEN_MONTH",
        )

        # 2. Test application data access type
        self.assertEqual(app.data_access_type, "THIRTEEN_MONTH")

        # 3. Test grant obj created OK.
        dag = DataAccessGrant.objects.get(beneficiary=user, application=app)
        #     Assert is not None
        self.assertNotEqual(dag, None)

        #     Assert expiration date has been set
        self.assertNotEqual(dag.expiration_date, None)

        # 4. Test token refresh is enabled for app
        ac = self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.OK,
        )

        # 5. Test that all calls are successful
        self._assert_call_all_fhir_endpoints(
            access_token=ac['access_token'], expected_response_code=HTTPStatus.OK
        )

        # 6. Mock a future date to test data access grant expiration.
        #    Test has_expired() is false before time change
        self.assertFalse(dag.has_expired())

        #    Mock future date 13 months and 2-days in future.
        StubDate.now = classmethod(
            lambda cls: datetime.now().replace(tzinfo=pytz.UTC)
            + relativedelta(months=+13, days=+2)
        )

        #    Test has_expired() is true after time change
        self.assertTrue(dag.has_expired())

        #    Test expiration_date is +13 months in future
        self.assertGreater(
            dag.expiration_date,
            datetime.now().replace(tzinfo=pytz.UTC)
            + relativedelta(months=+13, hours=-1),
        )

        # 7. Test token refresh is disabled when data access expired
        self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.UNAUTHORIZED,
            expected_response_error_mesg="invalid_grant",
            expected_response_error_description_mesg=settings.APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_EXPIRED_MESG,
        )

        # 8. Test that all calls fail when data access expired
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"],
            expected_response_code=HTTPStatus.UNAUTHORIZED,
            expected_response_detail_mesg=settings.APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_EXPIRED_MESG,
        )

        # 9. Test RE-AUTH works as expected in #10 thru end of tests.
        #    Note that the time was previously mocked +13 months & 2-days.

        # 10. Use helper method to create app, user, authorized grant & access token.
        user, app, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id_v2="-20140000008325",
            fhir_id_v3="-30140000008325",
            app_name="test_app1",
            app_username="devuser1",
            app_user_organization="org1",
            mbi=self._generate_random_mbi(),
            app_data_access_type="THIRTEEN_MONTH",
        )

        # 11. Test application data access type
        self.assertEqual(app.data_access_type, "THIRTEEN_MONTH")

        # 12. Test grant obj created OK.
        dag = DataAccessGrant.objects.get(beneficiary=user, application=app)
        #     Assert is not None
        self.assertNotEqual(dag, None)

        #     Assert expiration date has been set
        self.assertNotEqual(dag.expiration_date, None)

        #    Test expiration_date is +26 months in future
        self.assertGreater(
            dag.expiration_date,
            datetime.now().replace(tzinfo=pytz.UTC)
            + relativedelta(months=+26, days=-2),
        )

        # 13. Test token refresh is enabled for app
        ac = self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.OK,
        )

        # 14. Test that all calls are successful
        self._assert_call_all_fhir_endpoints(
            access_token=ac['access_token'], expected_response_code=HTTPStatus.OK
        )

    def test_data_access_grant_permissions_has_permission(self):
        """
        Test edge case bug fix for BB2-2130

        Previously, if a DataAccessGrant was removed, but there still
        existed an AccessToken, the following exception occurred:

        DataAccessGrant.DoesNotExist: DataAccessGrant matching query
          does not exist.
        """
        # 1. Use helper method to create app, user, authorized grant & access token.
        user, app, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id_v2="-20140000008325",
            fhir_id_v3="-30140000008325",
            app_name="test_app1",
            app_username="devuser1",
            app_user_organization="org1",
            mbi=self._generate_random_mbi(),
        )

        # 2. Test grant obj created OK.
        dag = DataAccessGrant.objects.get(beneficiary=user, application=app)
        #     Assert is not None
        self.assertNotEqual(dag, None)

        # 3. Copy access token
        copy_ac = AccessToken.objects.filter(token=ac["access_token"]).get()

        # 4. Test access token exist
        self.assertTrue(AccessToken.objects.filter(token=ac["access_token"]).exists())

        # 5. Test that all FHIR calls are successful
        self._assert_call_all_fhir_endpoints(
            access_token=ac['access_token'], expected_response_code=HTTPStatus.OK
        )

        # 6. Delete /revoke data access grant
        dag.delete()

        # 7. Restore access token
        copy_ac.save()

        # 8. Test access token is restored.
        self.assertTrue(AccessToken.objects.filter(token=ac["access_token"]).exists())

        # 9. Test that FHIR calls fail
        self._assert_call_all_fhir_endpoints(
            access_token=ac["access_token"],
            expected_response_code=HTTPStatus.FORBIDDEN,
            expected_response_detail_mesg="You do not have permission to perform this action.",
        )
