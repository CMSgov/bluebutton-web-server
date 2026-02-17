from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.http import HttpRequest
from apps.fhir.server.authentication import MatchFhirIdErrorType, MatchFhirIdResult, MatchFhirIdLookupType
from apps.fhir.bluebutton.models import Crosswalk
from apps.mymedicare_cb.constants import (
    DEFAULT_EMAIL,
    DEFAULT_HICN_HASH,
    DEFAULT_FIRST_NAME,
    DEFAULT_LAST_NAME,
    DEFAULT_USERNAME,
)
from apps.mymedicare_cb.models import BBMyMedicareCallbackCrosswalkCreateException
from apps.mymedicare_cb.authorization import OAuth2ConfigSLSx
from waffle.testutils import override_switch

from apps.mymedicare_cb.models import (
    create_beneficiary_record,
    get_and_update_user_from_initial_auth,
    get_and_update_from_refresh,
    _match_fhir_id_error_should_be_checked,
)
from unittest.mock import patch, Mock

from apps.versions import Versions

# Create the mock request
mock_request = Mock(spec=HttpRequest)

# Initialize session as a dictionary
mock_request.session = {'version': 2}


def search_fhir_id_by_identifier_side_effect(search_identifier, request, version) -> str:
    # Would try to retrieve these values via os envvars, but not sure what those look like in the jenkins pipeline
    if version == Versions.V1:
        return '-20140000008325'
    elif version == Versions.V2:
        return '-20140000008325'
    elif version == Versions.V3:
        return '-30250000008325'
    return '-20140000008325'


def match_fhir_id_side_effect_fail_v3(mbi, hicn_hash, request=None, version=Versions.NOT_AN_API_VERSION) -> MatchFhirIdResult:
    if version == Versions.V2:
        return MatchFhirIdResult(
            fhir_id='-20140000008325',
            lookup_type=MatchFhirIdLookupType.MBI
        )
    elif version == Versions.V3:
        return MatchFhirIdResult(
            error='Failure',
            error_type=MatchFhirIdErrorType.UPSTREAM,
            lookup_type=MatchFhirIdLookupType.MBI
        )
    return MatchFhirIdResult(
        fhir_id='-20140000008325',
        lookup_type=MatchFhirIdLookupType.MBI
    )


class BeneficiaryLoginTest(TestCase):

    def setUp(self):
        Group.objects.create(name='BlueButton')

    def test_create_beneficiary_record_full(self):
        args = {
            'username': DEFAULT_USERNAME,
            'user_hicn_hash': DEFAULT_HICN_HASH,
            'mbi': '1SA0A00AA00',
            'user_id_type': 'H',
            'fhir_id_v2': '-20000000002346',
            'fhir_id_v3': '-20000000002346',
            'first_name': DEFAULT_FIRST_NAME,
            'last_name': DEFAULT_LAST_NAME,
            'email': DEFAULT_EMAIL,
        }
        slsx_client = OAuth2ConfigSLSx(args)

        bene = create_beneficiary_record(slsx_client, fhir_id_v2=args['fhir_id_v2'], fhir_id_v3=args['fhir_id_v3'])
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args['username'])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args['user_hicn_hash'])
        self.assertEqual(bene.crosswalk.user_mbi, args['mbi'])
        self.assertEqual(bene.crosswalk.user_id_type, args['user_id_type'])
        self.assertEqual(bene.crosswalk.fhir_id(2), args['fhir_id_v2'])
        self.assertEqual(bene.crosswalk.fhir_id(3), args['fhir_id_v3'])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_create_beneficiary_record_min(self):
        args = {
            'username': '001010101010110',
            'user_hicn_hash': DEFAULT_HICN_HASH,
            'fhir_id_v2': '00001'
        }
        slsx_client = OAuth2ConfigSLSx(args)
        bene = create_beneficiary_record(slsx_client, fhir_id_v2=args['fhir_id_v2'])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args['user_hicn_hash'])
        self.assertEqual(bene.crosswalk.fhir_id_v2, args['fhir_id_v2'])

    def test_create_beneficiary_record_null_mbi(self):
        # Test creating new record with a None (Null) user_mbi value
        # This is OK. Handles the case where SLSx returns an empty mbi value.
        args = {
            'username': DEFAULT_USERNAME,
            'user_hicn_hash': DEFAULT_HICN_HASH,
            'user_mbi': None,
            'user_id_type': 'H',
            'fhir_id_v3': '0000001',
            'first_name': DEFAULT_FIRST_NAME,
            'last_name': DEFAULT_LAST_NAME,
            'email': DEFAULT_EMAIL,
        }
        slsx_client = OAuth2ConfigSLSx(args)
        bene = create_beneficiary_record(slsx_client, fhir_id_v3=args['fhir_id_v3'])
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args['username'])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args['user_hicn_hash'])
        self.assertEqual(bene.crosswalk.user_mbi, args['user_mbi'])
        self.assertEqual(bene.crosswalk.user_id_type, args['user_id_type'])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_create_beneficiary_record_no_mbi(self):
        # Test creating new record with NO user_mbi value
        # This is OK. Handles the case where SLSx returns an empty mbi value.
        args = {
            'username': DEFAULT_USERNAME,
            'user_hicn_hash': DEFAULT_HICN_HASH,
            'user_id_type': 'H',
            'fhir_id_v2': '000001',
            'first_name': DEFAULT_FIRST_NAME,
            'last_name': DEFAULT_LAST_NAME,
            'email': DEFAULT_EMAIL,
        }
        slsx_client = OAuth2ConfigSLSx(args)
        bene = create_beneficiary_record(slsx_client, fhir_id_v2=args['fhir_id_v2'])
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args['username'])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args['user_hicn_hash'])
        self.assertEqual(bene.crosswalk.user_mbi, None)
        self.assertEqual(bene.crosswalk.fhir_id_v2, args['fhir_id_v2'])
        self.assertEqual(bene.crosswalk.user_id_type, args['user_id_type'])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_fail_create_beneficiary_record(self):
        cases = {
            'empty username': {
                'args': {
                    'username': '',
                    'user_hicn_hash': DEFAULT_HICN_HASH,
                    'user_mbi': '1SA0A00AA00',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'email': DEFAULT_EMAIL,
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'username can not be None or empty string',
            },
            'missing username': {
                'args': {
                    'user_hicn_hash': DEFAULT_HICN_HASH,
                    'user_mbi': '1SA0A00AA00',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'email': DEFAULT_EMAIL,
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'username can not be None',
            },
            'missing hash': {
                'args': {
                    'username': DEFAULT_USERNAME,
                    'user_mbi': '1SA0A00AA00',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'email': DEFAULT_EMAIL,
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'user_hicn_hash can not be None',
            },
            'invalid_hicn_hash': {
                'args': {
                    'username': DEFAULT_USERNAME,
                    'user_mbi': '1SA0A00AA00',
                    'user_hicn_hash': '71f16b70b1b4fbdad76b',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'email': DEFAULT_EMAIL,
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'incorrect user HICN hash format',
            },
            # try to create a record with a len(user_mbi) > 11
            'invalid_mbi_too_long': {
                'args': {
                    'username': DEFAULT_USERNAME,
                    'user_hicn_hash': DEFAULT_HICN_HASH,
                    'mbi': '1SA0A00AA00000',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'email': DEFAULT_EMAIL,
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'incorrect user MBI format',
            },
            'empty string mbi': {
                'args': {
                    'username': DEFAULT_USERNAME,
                    'user_hicn_hash': DEFAULT_HICN_HASH,
                    'mbi': '',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'email': DEFAULT_EMAIL,
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'incorrect user MBI format',
            },
            'empty_fhir_id_v2': {
                'args': {
                    'username': DEFAULT_USERNAME,
                    'user_hicn_hash': DEFAULT_HICN_HASH,
                    'fhir_id_v2': '',
                    'user_id_type': 'H',
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'email': DEFAULT_EMAIL,
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'fhir_id_v2 can not be an empty string',
            },
            'empty_fhir_id_v3': {
                'args': {
                    'username': DEFAULT_USERNAME,
                    'user_hicn_hash': DEFAULT_HICN_HASH,
                    'fhir_id_v3': '',
                    'user_id_type': 'H',
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'email': DEFAULT_EMAIL,
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'fhir_id_v3 can not be an empty string',
            },
            'no_fhir_id': {
                'args': {
                    'username': DEFAULT_USERNAME,
                    'user_hicn_hash': DEFAULT_HICN_HASH,
                    'user_id_type': 'H',
                    'first_name': DEFAULT_FIRST_NAME,
                    'last_name': DEFAULT_LAST_NAME,
                    'email': DEFAULT_EMAIL,
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'a crosswalk must contain at least one valid fhir_id',
            }
        }
        for name, case in cases.items():
            slsx_client = OAuth2ConfigSLSx(case['args'])
            with self.assertRaisesRegex(case['exception'], case['exception_mesg']):
                create_beneficiary_record(slsx_client,
                                          fhir_id_v2=case['args'].get('fhir_id_v2', None),
                                          fhir_id_v3=case['args'].get('fhir_id_v3', None))

    def test_fail_create_multiple_beneficiary_record(self):
        cases = {
            'colliding username': {
                'args': [
                    {
                        'username': DEFAULT_USERNAME,
                        'user_hicn_hash': DEFAULT_HICN_HASH,
                        'user_id_type': 'H',
                        'fhir_id_v2': '-19990000000001',
                    },
                    {
                        'username': DEFAULT_USERNAME,
                        'user_hicn_hash': '60ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                        'user_id_type': 'H',
                        'fhir_id_v2': '-19990000000002',
                    },
                ],
                'exception': ValidationError,
                'exception_mesg': 'user already exists',
            },
            'colliding hicn_hash': {
                'args': [
                    {
                        'username': '10112233-4455-6677-8899-aabbccddeeff',
                        'user_hicn_hash': '70ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                        'user_id_type': 'H',
                        'fhir_id_v2': '-19990000000003',
                    },
                    {
                        'username': '20112233-4455-6677-8899-aabbccddeeff',
                        'user_hicn_hash': '70ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                        'user_id_type': 'H',
                        'fhir_id_v2': '-19990000000004',
                    },
                ],
                'exception': ValidationError,
                'exception_mesg': 'user_hicn_hash already exists',
            },
            'colliding mbi': {
                'args': [
                    {
                        'username': '60112233-4455-6677-8899-aabbccddeeff',
                        'user_hicn_hash': 'a0ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                        'mbi': '1SA0A00AA00',
                        'user_id_type': 'H',
                        'fhir_id_v2': '-19990000000006',
                    },
                    {
                        'username': '70112233-4455-6677-8899-aabbccddeeff',
                        'user_hicn_hash': 'a0bd63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                        'mbi': '1SA0A00AA00',
                        'user_id_type': 'H',
                        'fhir_id_v2': '-19990000000007',
                    },
                ],
                'exception': ValidationError,
                'exception_mesg': 'mbi already exists',
            },
            'colliding fhir_id_v2': {
                'args': [
                    {
                        'username': '30112233-4455-6677-8899-aabbccddeeff',
                        'user_hicn_hash': '80ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                        'fhir_id_v2': '-19990000000005',
                    },
                    {
                        'username': '40112233-4455-6677-8899-aabbccddeeff',
                        'user_hicn_hash': '90ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                        'fhir_id_v2': '-19990000000005',
                    },
                ],
                'exception': ValidationError,
                'exception_mesg': 'fhir_id_v2 already exists',
            },
            'colliding fhir_id_v3': {
                'args': [
                    {
                        'username': '48112233-4455-6677-8899-aabbccddeeff',
                        'user_hicn_hash': '80ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad764',
                        'fhir_id_v3': '-19990000000005',
                    },
                    {
                        'username': '49112233-4455-6677-8899-aabbccddeeff',
                        'user_hicn_hash': '90ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad763',
                        'fhir_id_v3': '-19990000000005',
                    },
                ],
                'exception': ValidationError,
                'exception_mesg': 'fhir_id_v3 already exists',
            }
        }

        for name, case in cases.items():
            arg0 = case['args'][0]
            slsx_client0 = OAuth2ConfigSLSx(case['args'][0])
            create_beneficiary_record(slsx_client0,
                                      fhir_id_v2=arg0.get('fhir_id_v2', None),
                                      fhir_id_v3=arg0.get('fhir_id_v3', None))
            with self.assertRaisesRegex(case['exception'], case['exception_mesg']):
                arg1 = case['args'][1]
                slsx_client1 = OAuth2ConfigSLSx(arg1)
                create_beneficiary_record(slsx_client1,
                                          fhir_id_v2=arg1.get('fhir_id_v2', None),
                                          fhir_id_v3=arg1.get('fhir_id_v3', None))

    @patch('apps.mymedicare_cb.models.match_fhir_id', return_value=(MatchFhirIdResult(
                                                                    fhir_id='-20000000002346',
                                                                    lookup_type=MatchFhirIdLookupType.MBI)))
    @patch('apps.fhir.bluebutton.models.ArchivedCrosswalk.create')
    def test_user_mbi_updated_from_null(self, mock_archive, mock_match_fhir) -> None:
        """Test that user_mbi gets updated when previously null"""
        fake_user = User.objects.create_user(
            username=DEFAULT_USERNAME,
            email=DEFAULT_EMAIL
        )
        slsx_mbi = '1S00EU7JH82'

        crosswalk = Crosswalk.objects.create(
            user=fake_user,
            fhir_id_v2='-20000000002346',
            user_hicn_hash=DEFAULT_HICN_HASH,
            user_mbi=None,
            user_id_type='M'
        )

        slsx_client = Mock(spec=OAuth2ConfigSLSx)
        slsx_client.user_id = DEFAULT_USERNAME
        slsx_client.mbi = slsx_mbi
        slsx_client.hicn_hash = DEFAULT_HICN_HASH

        user, crosswalk_type = get_and_update_user_from_initial_auth(slsx_client, mock_request)

        user.refresh_from_db()
        crosswalk.refresh_from_db()
        self.assertEqual(user.crosswalk.user_mbi, slsx_mbi)
        mock_archive.assert_called_once()

    @patch('apps.mymedicare_cb.models.match_fhir_id', return_value=(MatchFhirIdResult(
                                                                    fhir_id='-20000000002346',
                                                                    lookup_type=MatchFhirIdLookupType.MBI)))
    @patch('apps.fhir.bluebutton.models.ArchivedCrosswalk.create')
    def test_user_mbi_updated_from_different_value(self, mock_archive, mock_match_fhir) -> None:
        """Test that user_mbi gets updated when previously a different value"""
        fake_user = User.objects.create_user(
            username=DEFAULT_USERNAME,
            email=DEFAULT_EMAIL
        )
        slsx_mbi = '1S00EU7JH82'

        crosswalk = Crosswalk.objects.create(
            user=fake_user,
            fhir_id_v2='-20000000002346',
            user_hicn_hash=DEFAULT_HICN_HASH,
            user_mbi='1S00EU7JH00',
            user_id_type='M'
        )

        slsx_client = Mock(spec=OAuth2ConfigSLSx)
        slsx_client.user_id = DEFAULT_USERNAME
        slsx_client.mbi = slsx_mbi
        slsx_client.hicn_hash = DEFAULT_HICN_HASH

        user, crosswalk_type = get_and_update_user_from_initial_auth(slsx_client, mock_request)

        user.refresh_from_db()
        crosswalk.refresh_from_db()
        self.assertEqual(user.crosswalk.user_mbi, slsx_mbi)
        mock_archive.assert_called_once()

    @patch('apps.fhir.server.authentication.search_fhir_id_by_identifier', side_effect=search_fhir_id_by_identifier_side_effect)
    @patch('apps.fhir.bluebutton.models.ArchivedCrosswalk.create')
    @override_switch('v3_endpoints', active=True)
    def test_get_and_update_from_refresh_fhir_id_v3_previously_null(self, mock_archive, mock_match_fhir) -> None:
        """Test that the get_and_update_from_refresh executes fields correctly,
        specifically in this test, fhir_id_v3
        """
        user_hicn_hash = DEFAULT_HICN_HASH
        user_mbi = '1S00EU7JH00'
        fhir_id_v2 = '-20140000008325'
        username = DEFAULT_USERNAME

        fake_user = User.objects.create_user(
            username=username,
            email='fu@bar.bar'
        )

        crosswalk = Crosswalk.objects.create(
            user=fake_user,
            fhir_id_v2=fhir_id_v2,
            user_hicn_hash=user_hicn_hash,
            user_mbi=user_mbi,
            user_id_type='M'
        )
        # Confirm fhir_id_v3 is None before calling the function
        assert crosswalk.fhir_id_v3 is None

        user, crosswalk_type = get_and_update_from_refresh(user_mbi, username, user_hicn_hash, mock_request)

        assert user.crosswalk.fhir_id_v3 == '-30250000008325'

    @patch('apps.fhir.server.authentication.search_fhir_id_by_identifier', side_effect=search_fhir_id_by_identifier_side_effect)
    @patch('apps.fhir.bluebutton.models.ArchivedCrosswalk.create')
    def test_get_and_update_from_refresh_fhir_id_v2_previously_null(self, mock_archive, mock_match_fhir) -> None:
        """Test that the get_and_update_from_refresh executes fields correctly,
        specifically in this test, fhir_id_v2
        """
        user_hicn_hash = DEFAULT_HICN_HASH
        user_mbi = '1S00EU7JH00'
        fhir_id_v3 = '-30250000008325'
        username = DEFAULT_USERNAME

        fake_user = User.objects.create_user(
            username=username,
            email='fu@bar.bar'
        )

        crosswalk = Crosswalk.objects.create(
            user=fake_user,
            fhir_id_v3=fhir_id_v3,
            user_hicn_hash=user_hicn_hash,
            user_mbi=user_mbi,
            user_id_type='M'
        )
        # Confirm fhir_id_v3 is None before calling the function
        assert crosswalk.fhir_id_v2 is None

        user, crosswalk_type = get_and_update_from_refresh(user_mbi, username, user_hicn_hash, mock_request)

        assert user.crosswalk.fhir_id_v2 == '-20140000008325'

    def test_match_fhir_id_error_should_be_checked_v1_call_failure(self) -> None:
        result = _match_fhir_id_error_should_be_checked(Versions.V1, Versions.V2)
        assert result

    def test_match_fhir_id_error_should_be_checked_v2_call(self) -> None:
        result = _match_fhir_id_error_should_be_checked(Versions.V2, Versions.V2)
        assert result

    def test_match_fhir_id_error_should_be_checked_v3_call(self) -> None:
        result = _match_fhir_id_error_should_be_checked(Versions.V3, Versions.V3)
        assert result

    def test_match_fhir_id_error_should_be_checked_v1_v3_call(self) -> None:
        result = _match_fhir_id_error_should_be_checked(Versions.V1, Versions.V3)
        assert not result

    @patch('apps.mymedicare_cb.models.match_fhir_id', side_effect=match_fhir_id_side_effect_fail_v3)
    def test_v2_auth_flow_when_v3_match_fhir_id_call_fails(self, mock_match_fhir) -> None:
        """During v2 auth flow, if match_fhir_id for v3 throws and error, the execution of
        __get_and_update_user should continue, and a crosswalk record should be created,
        if no record already exists for the user.
        """

        slsx_client = Mock(spec=OAuth2ConfigSLSx)
        slsx_client.user_id = DEFAULT_USERNAME
        slsx_client.mbi = '1S00EU7JH82'
        slsx_client.hicn_hash = DEFAULT_HICN_HASH
        slsx_client.firstname = DEFAULT_FIRST_NAME
        slsx_client.lastname = DEFAULT_LAST_NAME
        slsx_client.email = DEFAULT_EMAIL

        user, crosswalk_type = get_and_update_user_from_initial_auth(slsx_client, mock_request)
        self.assertIsNotNone(user.crosswalk)
        self.assertEqual(crosswalk_type, 'C')
        self.assertIsNone(user.crosswalk.fhir_id_v3)
