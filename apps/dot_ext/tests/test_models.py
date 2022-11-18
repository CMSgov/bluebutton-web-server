from datetime import datetime
import pytz
from django.contrib.auth.models import User
from oauth2_provider.models import get_application_model

from apps.dot_ext.models import (
    get_application_counts,
    get_application_require_demographic_scopes_count,
)
from apps.test import BaseApiTest


class TestDotExtModels(BaseApiTest):
    def test_application_data_access_fields(self):
        """
        BB2-1774 Test the CRUD operations & validation
        on new data access fields from apps.dot_ext.models
        """
        # Create dev user for tests.
        dev_user = self._create_user("john", "123456")

        # Create defaults
        test_app = self._create_application("test_app", user=dev_user)
        self.assertEqual("ONE_TIME", test_app.type)
        self.assertEqual(None, test_app.end_date)

        # Delete app
        test_app.delete()

        # Create for ONE_TIME
        test_app = self._create_application(
            "test_app", user=dev_user, data_access_type="ONE_TIME"
        )

        self.assertEqual("ONE_TIME", test_app.type)
        self.assertEqual(None, test_app.end_date)

        # Create for THIRTEEN_MONTH
        test_app = self._create_application(
            "test_app", user=dev_user, data_access_type="THIRTEEN_MONTH"
        )

        self.assertEqual("THIRTEEN_MONTH", test_app.type)
        self.assertEqual(None, test_app.end_date)

        # Create Invalid data_access_type is not valid.
        with self.assertRaisesRegex(
            ValueError, "Invalid data_access_type: BAD_DATA_ACCESS_TYPE"
        ):
            test_app = self._create_application(
                "test_app", user=dev_user, data_access_type="BAD_DATA_ACCESS_TYPE"
            )

        # Create ONE_TIME w/ end_date is not valid.
        with self.assertRaisesRegex(
            ValueError, "An end_date is ONLY required for the RESEARCH_STUDY type!"
        ):
            test_app = self._create_application(
                "test_app",
                user=dev_user,
                data_access_type="ONE_TIME",
                end_date=datetime(2030, 1, 15, 0, 0, 0, 0, pytz.UTC),
            )

        # Create THIRTEEN_MONTH w/ end_date is not valid.
        with self.assertRaisesRegex(
            ValueError, "An end_date is ONLY required for the RESEARCH_STUDY type!"
        ):
            test_app = self._create_application(
                "test_app",
                user=dev_user,
                data_access_type="ONE_TIME",
                end_date=datetime(2030, 1, 15, 0, 0, 0, 0, pytz.UTC),
            )

        # Create for RESEARCH_STUDY w/o end_date is not valid.
        with self.assertRaisesRegex(
            ValueError, "An end_date is required for the RESEARCH_STUDY type!"
        ):
            test_app = self._create_application(
                "test_app", user=dev_user, data_access_type="RESEARCH_STUDY"
            )

        # Create for RESEARCH_STUDY w/ end_date is valid.
        test_app = self._create_application(
            "test_app",
            user=dev_user,
            data_access_type="RESEARCH_STUDY",
            end_date=datetime(2030, 1, 15, 0, 0, 0, 0, pytz.UTC),
        )
        self.assertEqual("RESEARCH_STUDY", test_app.type)
        self.assertEqual("2030-01-15 00:00:00+00:00", str(test_app.end_date))

        # Update invalid data_access_type choice is not valid.
        with self.assertRaisesRegex(
            ValueError, "Invalid data_access_type: BAD_DATA_ACCESS_TYPE"
        ):
            test_app.type = "BAD_DATA_ACCESS_TYPE"
            test_app.save()

        # Update ONE_TIME w/ end_date (already set) is not valid.
        with self.assertRaisesRegex(
            ValueError, "An end_date is ONLY required for the RESEARCH_STUDY type!"
        ):
            test_app.type = "ONE_TIME"
            test_app.save()

        # Update ONE_TIME w/o end_date is valid.
        test_app.type = "ONE_TIME"
        test_app.end_date = None
        test_app.save()
        self.assertEqual("ONE_TIME", test_app.type)
        self.assertEqual(None, test_app.end_date)

        # Update THIRTEEN_MONTH w/o end_date is valid.
        test_app.type = "THIRTEEN_MONTH"
        test_app.end_date = None
        test_app.save()
        self.assertEqual("THIRTEEN_MONTH", test_app.type)
        self.assertEqual(None, test_app.end_date)

        # Update RESEARCH_STUDY w/o end_date is not valid.
        with self.assertRaisesRegex(
            ValueError, "An end_date is required for the RESEARCH_STUDY type!"
        ):
            test_app.type = "RESEARCH_STUDY"
            test_app.end_date = None
            test_app.save()

        # Update RESEARCH_STUDY w/ end_date is valid.
        test_app.type = "RESEARCH_STUDY"
        test_app.end_date = datetime(2029, 1, 25, 0, 0, 0, 0, pytz.UTC)
        self.assertEqual("RESEARCH_STUDY", test_app.type)
        self.assertEqual("2029-01-25 00:00:00+00:00", str(test_app.end_date))

    def test_application_count_funcs(self):
        """
        Test the get_application_active_counts() function
        from apps.dot_ext.models
        """
        Application = get_application_model()

        redirect_uri = "http://localhost"

        # create capabilities
        capability_a = self._create_capability("Capability A", [])
        capability_b = self._create_capability("Capability B", [])

        # Create 5x active applications with require_demographi_scopes=True (Default)
        dev_user = User.objects.create_user("dev", password="123456")
        for cnt in range(5):
            app = self._create_application(
                "application_" + str(cnt),
                grant_type=Application.GRANT_AUTHORIZATION_CODE,
                user=dev_user,
                redirect_uris=redirect_uri,
            )
            app.scope.add(capability_a, capability_b)
            app.save()

        # Create 2x active applications with require_demographic_scopes=False.
        for cnt in range(5, 7):
            app = self._create_application(
                "application_" + str(cnt),
                grant_type=Application.GRANT_AUTHORIZATION_CODE,
                user=dev_user,
                redirect_uris=redirect_uri,
            )
            app.require_demographic_scopes = False
            app.scope.add(capability_a, capability_b)
            app.save()

        # Create 3x in-active applications.
        dev_user = User.objects.create_user("dev3", password="123456")
        for cnt in range(3):
            app = self._create_application(
                "application_" + str(cnt),
                grant_type=Application.GRANT_AUTHORIZATION_CODE,
                user=dev_user,
                redirect_uris=redirect_uri,
            )
            app.scope.add(capability_a, capability_b)
            app.active = False
            app.save()

        # Assert app counts
        self.assertEqual(
            "{'active_cnt': 7, 'inactive_cnt': 3}", str(get_application_counts())
        )

        # Assert app count requiring demo scopes
        self.assertEqual(5, get_application_require_demographic_scopes_count())
