import json
from unittest.mock import Mock

from django.contrib import admin
from django.contrib.auth.models import User
from oauth2_provider.models import get_access_token_model, get_application_model

import apps.logging.request_logger as logging
from apps.authorization.models import ArchivedDataAccessGrant, DataAccessGrant
from apps.constants import DEFAULT_SAMPLE_FHIR_ID_V2, DEFAULT_SAMPLE_FHIR_ID_V3
from apps.dot_ext.admin import MyApplicationAdmin
from apps.dot_ext.models import (
    AccessTokenExtension,
    Application,
    InternalApplicationLabels,
    get_application_counts,
    get_application_require_demographic_scopes_count,
)
from apps.logging.utils import cleanup_logger, get_log_content, redirect_loggers
from apps.test import BaseApiTest

AccessToken = get_access_token_model()


class TestDotExtModels(BaseApiTest):
    fixtures = ['internal_application_labels.json']

    def setUp(self):
        self.logger_registry = redirect_loggers()
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])

    def tearDown(self):
        cleanup_logger(self.logger_registry)

    def test_application_data_access_fields(self):
        """
        Test the CRUD operations & validation
        on new data access fields from apps.dot_ext.models
        """
        # Create dev user for tests.
        dev_user = self._create_user('john', '123456')

        # Create defaults
        test_app = self._create_application('test_app', user=dev_user)
        self.assertEqual('THIRTEEN_MONTH', test_app.data_access_type)

        # Delete app
        test_app.delete()

        # Create for ONE_TIME
        test_app = self._create_application('test_app', user=dev_user, data_access_type='ONE_TIME')

        self.assertEqual('ONE_TIME', test_app.data_access_type)

        # Create for THIRTEEN_MONTH
        test_app = self._create_application('test_app', user=dev_user, data_access_type='THIRTEEN_MONTH')

        self.assertEqual('THIRTEEN_MONTH', test_app.data_access_type)

        # Create Invalid data_access_type is not valid.
        with self.assertRaisesRegex(ValueError, 'Invalid data_access_type: BAD_DATA_ACCESS_TYPE'):
            test_app = self._create_application('test_app', user=dev_user, data_access_type='BAD_DATA_ACCESS_TYPE')

        # Update invalid data_access_type choice is not valid.
        with self.assertRaisesRegex(ValueError, 'Invalid data_access_type: BAD_DATA_ACCESS_TYPE'):
            test_app.data_access_type = 'BAD_DATA_ACCESS_TYPE'
            test_app.save()

    def test_application_data_access_type_change(self):
        """
        Test the application.data_access_type change, make sure the change is logged
        """
        # Create dev user for tests.
        dev_user = self._create_user('john', '123456')

        # Create defaults
        test_app = self._create_application('test_app', user=dev_user)
        self.assertEqual('THIRTEEN_MONTH', test_app.data_access_type)

        # fake some grants tied to the user and the app
        DataAccessGrant.objects.update_or_create(beneficiary=User.objects.get(username='john'), application=test_app)

        grants = DataAccessGrant.objects.filter(application__name='test_app')

        self.assertIsNotNone(grants)
        self.assertTrue(grants.count() > 0)

        # application.data_access_type changed from ONE_TIME to RESEARCH_STUDY
        # w/ end_date is valid.
        test_app.data_access_type = 'RESEARCH_STUDY'
        self.assertEqual('RESEARCH_STUDY', test_app.data_access_type)
        test_app.save()

        try:
            DataAccessGrant.objects.get(application__name='test_app')
        except DataAccessGrant.DoesNotExist:
            self.fail("Expecting grants for 'test_app' to carry over, no existing grants should be affected.")

        log_content = get_log_content(self.logger_registry, logging.AUDIT_APPLICATION_TYPE_CHANGE)
        self.assertIsNotNone(log_content)
        log_entries = log_content.splitlines()
        self.assertEqual(len(log_entries), 1)
        log_entry_json = json.loads(log_entries[0])
        self.assertEqual(log_entry_json['type'], 'application_data_access_type_change')
        self.assertEqual(log_entry_json['data_access_type_old'], 'THIRTEEN_MONTH')
        self.assertEqual(log_entry_json['data_access_type_new'], 'RESEARCH_STUDY')

    def test_application_data_access_type_change_switch_off(self):
        """
        Test the application.data_access_type change, access grants will not be affected
        """
        # Create dev user for tests.
        dev_user = self._create_user('john', '123456')

        # Create defaults
        test_app_sw_off = self._create_application('test_app_sw_off', user=dev_user)
        self.assertEqual('THIRTEEN_MONTH', test_app_sw_off.data_access_type)

        # fake some grants tied to the user and the app
        DataAccessGrant.objects.update_or_create(
            beneficiary=User.objects.get(username='john'), application=test_app_sw_off
        )

        grants = DataAccessGrant.objects.filter(application__name='test_app_sw_off')

        self.assertTrue(grants.count() > 0)

        # application.data_access_type changed from ONE_TIME to RESEARCH_STUDY
        # w/ end_date is valid.
        test_app_sw_off.data_access_type = 'RESEARCH_STUDY'
        self.assertEqual('RESEARCH_STUDY', test_app_sw_off.data_access_type)

        test_app_sw_off.save()

        try:
            grants = DataAccessGrant.objects.get(application__name='test_app_sw_off')
        except DataAccessGrant.DoesNotExist:
            self.fail("Expecting grants for 'test_app_sw_off' NOT changed.")

        self.assertIsNotNone(grants)

        archived_grants = ArchivedDataAccessGrant.objects.filter(application__name='test_app_sw_off')

        self.assertTrue(archived_grants.count() == 0)

        log_content = get_log_content(self.logger_registry, logging.AUDIT_APPLICATION_TYPE_CHANGE)

        # this will be logged
        self.assertTrue(log_content)

    def test_application_count_funcs(self):
        """
        Test the get_application_active_counts() function
        from apps.dot_ext.models
        """
        Application = get_application_model()

        redirect_uri = 'http://localhost'

        # create capabilities
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])

        # Create 5x active applications with require_demographi_scopes=True (Default)
        dev_user = User.objects.create_user('dev', password='123456')
        for cnt in range(5):
            app = self._create_application(
                'application_' + str(cnt),
                grant_type=Application.GRANT_AUTHORIZATION_CODE,
                user=dev_user,
                redirect_uris=redirect_uri,
            )
            app.scope.add(capability_a, capability_b)
            app.save()

        # Create 2x active applications with require_demographic_scopes=False.
        for cnt in range(5, 7):
            app = self._create_application(
                'application_' + str(cnt),
                grant_type=Application.GRANT_AUTHORIZATION_CODE,
                user=dev_user,
                redirect_uris=redirect_uri,
            )
            app.require_demographic_scopes = False
            app.scope.add(capability_a, capability_b)
            app.save()

        # Create 3x in-active applications.
        dev_user = User.objects.create_user('dev3', password='123456')
        for cnt in range(3):
            app = self._create_application(
                'application_' + str(cnt),
                grant_type=Application.GRANT_AUTHORIZATION_CODE,
                user=dev_user,
                redirect_uris=redirect_uri,
            )
            app.scope.add(capability_a, capability_b)
            app.active = False
            app.save()

        # Assert app counts
        self.assertEqual("{'active_cnt': 7, 'inactive_cnt': 3}", str(get_application_counts()))

        # Assert app count requiring demo scopes
        self.assertEqual(5, get_application_require_demographic_scopes_count())

    def test_internal_application_labels_switch_on(self):
        """
        Test the Application model creation
        check the 'internal_application_labels' field present
        """
        # Create dev user for tests.
        dev_user = self._create_user('john', '123456')

        # Create defaults
        test_app = self._create_application('test_app', user=dev_user)
        self.assertTrue(hasattr(test_app, 'internal_application_labels'))

    def test_internal_application_labels_load(self):
        """
        Test the InternalApplicationLabels model creation and load with values from the fixture
        """
        internal_labels = InternalApplicationLabels.objects.all()
        self.assertIsNotNone(internal_labels)
        self.assertEqual(len(internal_labels), 11)

    def test_internal_application_labels_getter(self):
        """
        Test the getter of the many to many field 'internal_application_labels'
        """
        internal_labels = InternalApplicationLabels.objects.all()
        self.assertIsNotNone(internal_labels)
        self.assertEqual(len(internal_labels), 11)

        # Create dev user for tests.
        dev_user = self._create_user('john', '123456')

        # Create app
        test_app = self._create_application('test_app', user=dev_user)
        l1 = internal_labels[0]
        l3 = internal_labels[2]
        l5 = internal_labels[4]
        l11 = internal_labels[10]
        test_app.internal_application_labels.add(l1, l3, l5)
        labels = test_app.get_internal_application_labels()
        self.assertTrue(l1.slug in labels)
        self.assertTrue(l3.slug in labels)
        self.assertTrue(l5.slug in labels)
        self.assertTrue(l11.slug not in labels)

    def test_internal_application_labels_admin(self):
        """
        Test 'internal_application_labels' wrapped in admin model
        """
        internal_labels = InternalApplicationLabels.objects.all()
        self.assertIsNotNone(internal_labels)
        self.assertEqual(len(internal_labels), 11)

        # Create dev user for tests.
        dev_user = self._create_user('john', '123456')

        # Create app bound with internal_application_labels
        test_app = self._create_application('test_app', user=dev_user)
        l1 = internal_labels[0]
        l3 = internal_labels[2]
        l5 = internal_labels[4]
        l11 = internal_labels[10]
        test_app.internal_application_labels.add(l1, l3, l5)

        app_admin = MyApplicationAdmin(Application, admin.site)

        list_display = app_admin.get_list_display(None)
        self.assertIn('get_internal_application_labels', list_display)

        search_fields = app_admin.get_search_fields(None)
        self.assertIn('internal_application_labels__label', search_fields)

        request = Mock(user=dev_user)

        field_sets = app_admin.get_fieldsets(request, None)
        self.assertIn('internal_application_labels', str(field_sets))

        internal_labels = app_admin.get_internal_application_labels(test_app)
        self.assertTrue(l1.slug in internal_labels)
        self.assertTrue(l3.slug in internal_labels)
        self.assertTrue(l5.slug in internal_labels)
        self.assertTrue(l11.slug not in internal_labels)

    def test_access_token_extension_is_created(self) -> None:
        """Ensure that when an access token is saved, a corresponding AccessTokenExtension record
        is created
        """

        first_access_token = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Coverage.search patient/Patient.search patient/ExplanationOfBenefit.search'
        ac.save()
        access_token_extension = AccessTokenExtension.objects.get(access_token=ac)

        assert access_token_extension is not None
        assert access_token_extension.access_token == ac

    def test_access_token_extension_is_deleted_when_token_is_deleted(self) -> None:
        """Ensure that when an access token is deleted, the corresponding AccessTokenExtension record
        is deleted
        """

        first_access_token = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Coverage.search patient/Patient.search patient/ExplanationOfBenefit.search'
        ac.save()
        access_token_extension = AccessTokenExtension.objects.get(access_token=ac)
        access_token_extension_id = access_token_extension.id

        assert access_token_extension is not None
        assert access_token_extension.access_token == ac

        ac.delete()

        with self.assertRaises(AccessTokenExtension.DoesNotExist):
            access_token_extension = AccessTokenExtension.objects.get(id=access_token_extension_id)
