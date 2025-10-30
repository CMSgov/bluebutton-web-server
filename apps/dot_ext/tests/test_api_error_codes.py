from apps.test import BaseApiTest
from http import HTTPStatus
import json
import pytz
from random import randint
from apps.authorization.models import (
    DataAccessGrant,
)
from apps.constants import AccessType
from datetime import datetime
from dateutil.relativedelta import relativedelta
from unittest import mock


class StubDate(datetime):
    pass


# These tests cover `validate_app_is_active` in `utils.py`
# In particular, they cover whether or not we get the right error
# codes back for a given call/situation.
class TestDataAccessPermissions(BaseApiTest):

    # In this test, we should get back a `HTTPStatus.UNAUTHORIZED` when we try
    # and refresh the token on a ONE_TIME application.
    def test_one_time_access_unauthorized_to_refresh(self):
        refresh_responses = [
            {
                "app_data_access_type": AccessType.ONE_TIME,
                "status_code": HTTPStatus.FORBIDDEN,
                "expected_in": "User data access grant expired"
            },
            {
                "app_data_access_type": AccessType.RESEARCH_STUDY,
                "status_code": HTTPStatus.OK,
                "expected_in": " "
            },
            {
                "app_data_access_type": AccessType.THIRTEEN_MONTH,
                "status_code": HTTPStatus.OK,
                "expected_in": " "
            }
        ]
        for test in refresh_responses:
            # Create a random suffix, so we're not testing repeatedly against
            # the same app in the database.
            suffix = randint(1000, 9999)
            user, app, ac = self._create_user_app_token_grant(
                first_name="First",
                last_name=f"Last_{suffix}",
                fhir_id_v2=f"-2014000000{suffix}",
                fhir_id_v3=f"-3014000000{suffix}",
                app_name=f"test_app_{suffix}",
                app_username=f"devuser_{suffix}",
                app_user_organization=f"org_{suffix}",
                mbi=self._generate_random_mbi(),
                app_data_access_type=test["app_data_access_type"],
            )
            ac = self._assert_call_token_refresh_endpoint(
                application=app,
                refresh_token=ac["refresh_token"],
                expected_response_code=test["status_code"]
            )

    def test_not_found_on_dag_revocation(self):
        # Given a THIRTEEN_MONTH, we should get back an NOT_FOUND
        # if the DAG has been revoked or otherwise removed.
        suffix = randint(1000, 9999)
        user, app, ac = self._create_user_app_token_grant(
            first_name="First",
            last_name=f"Last_{suffix}",
            fhir_id_v2=f"-2014000000{suffix}",
            fhir_id_v3=f"-3014000000{suffix}",
            app_name=f"test_app_{suffix}",
            app_username=f"devuser_{suffix}",
            app_user_organization=f"org_{suffix}",
            mbi=self._generate_random_mbi(),
            app_data_access_type=AccessType.THIRTEEN_MONTH,
        )

        # Get the DAG, so we can delete it (revoke it)
        dag = DataAccessGrant.objects.get(beneficiary=user, application=app)
        dag.delete()

        # Now, we should get back a 401
        ac = self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.FORBIDDEN,
            expected_in_err_mesg="Data access grant cannot be found"
        )

    @mock.patch("apps.authorization.models.datetime", StubDate)
    def test_unauthorized_when_dag_expired(self):
        # Given a THIRTEEN_MONTH, we should get back an UNAUTHORIZED
        # if the DAG has expired.
        suffix = randint(1000, 9999)
        user, app, ac = self._create_user_app_token_grant(
            first_name="First",
            last_name=f"Last_{suffix}",
            fhir_id_v2=f"-2014000000{suffix}",
            fhir_id_v3=f"-3014000000{suffix}",
            app_name=f"test_app_{suffix}",
            app_username=f"devuser_{suffix}",
            app_user_organization=f"org_{suffix}",
            mbi=self._generate_random_mbi(),
            app_data_access_type=AccessType.THIRTEEN_MONTH,
        )

        #    Mock future date 13 months and 2-days in future.
        StubDate.now = classmethod(
            lambda cls: datetime.now().replace(tzinfo=pytz.UTC)
            + relativedelta(months=+13, days=+2)
        )
        # Now, we should get back a 401 because we are in the future soon
        ac = self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.FORBIDDEN,
            expected_in_err_mesg="User data access grant expired"
        )

    def test_app_not_active(self):
        # Given an app, but the app is not active, we should return UNAUTHORIZED.
        suffix = randint(1000, 9999)
        user, app, ac = self._create_user_app_token_grant(
            first_name="First",
            last_name=f"Last_{suffix}",
            fhir_id_v2=f"-2014000000{suffix}",
            fhir_id_v3=f"-3014000000{suffix}",
            app_name=f"test_app_{suffix}",
            app_username=f"devuser_{suffix}",
            app_user_organization=f"org_{suffix}",
            mbi=self._generate_random_mbi(),
            app_data_access_type=AccessType.THIRTEEN_MONTH,
        )

        app.active = False
        app.save()

        # Now, we should get back a 401 because we are in the future soon
        ac = self._assert_call_token_refresh_endpoint(
            application=app,
            refresh_token=ac["refresh_token"],
            expected_response_code=HTTPStatus.FORBIDDEN,
            expected_in_err_mesg="is temporarily inactive"
        )

    def _assert_call_token_refresh_endpoint(
        self,
        application=None,
        refresh_token=None,
        expected_response_code=None,
        expected_response_error_mesg=None,
        expected_response_error_description_mesg=None,
        expected_in_err_mesg=None
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
        response = self.client.post("/v1/o/token/", data=refresh_post_data)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, expected_response_code)
        if expected_response_error_mesg is not None:
            self.assertEqual(content["error"], expected_response_error_mesg)
        if expected_response_error_description_mesg is not None:
            self.assertEqual(
                content["error_description"], expected_response_error_description_mesg
            )
        if expected_in_err_mesg is not None:
            self.assertIn(expected_in_err_mesg, content["error_description"])
        return content
