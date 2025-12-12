from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.http import HttpRequest
from apps.fhir.server.authentication import MatchFhirIdResult, MatchFhirIdLookupType
from apps.fhir.bluebutton.models import Crosswalk
from apps.mymedicare_cb.models import BBMyMedicareCallbackCrosswalkCreateException
from apps.mymedicare_cb.authorization import OAuth2ConfigSLSx

from ..models import create_beneficiary_record, get_and_update_user
from unittest.mock import patch, Mock

# Create the mock request
mock_request = Mock(spec=HttpRequest)

# Initialize session as a dictionary
mock_request.session = {'version': 2}


class BeneficiaryLoginTest(TestCase):

    def setUp(self):
        Group.objects.create(name='BlueButton')

    def test_create_beneficiary_record_full(self):
        args = {
            'username': '00112233-4455-6677-8899-aabbccddeeff',
            'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
            'mbi': '1SA0A00AA00',
            'user_id_type': 'H',
            'fhir_id_v2': '-20000000002346',
            'fhir_id_v3': '-20000000002346',
            'first_name': 'Hello',
            'last_name': 'World',
            'email': 'oscar@sesamestreet.gov',
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
            'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
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
            'username': '00112233-4455-6677-8899-aabbccddeeff',
            'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
            'user_mbi': None,
            'user_id_type': 'H',
            'fhir_id_v3': '0000001',
            'first_name': 'Hello',
            'last_name': 'World',
            'email': 'oscar@sesamestreet.gov',
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
            'username': '00112233-4455-6677-8899-aabbccddeeff',
            'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
            'user_id_type': 'H',
            'fhir_id_v2': '000001',
            'first_name': 'Hello',
            'last_name': 'World',
            'email': 'oscar@sesamestreet.gov',
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
                    'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                    'user_mbi': '1SA0A00AA00',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': 'Hello',
                    'last_name': 'World',
                    'email': 'oscar@sesamestreet.gov',
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'username can not be None or empty string',
            },
            'missing username': {
                'args': {
                    'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                    'user_mbi': '1SA0A00AA00',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': 'Hello',
                    'last_name': 'World',
                    'email': 'oscar@sesamestreet.gov',
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'username can not be None',
            },
            'missing hash': {
                'args': {
                    'username': '00112233-4455-6677-8899-aabbccddeeff',
                    'user_mbi': '1SA0A00AA00',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': 'Hello',
                    'last_name': 'World',
                    'email': 'oscar@sesamestreet.gov',
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'user_hicn_hash can not be None',
            },
            'invalid_hicn_hash': {
                'args': {
                    'username': '00112233-4455-6677-8899-aabbccddeeff',
                    'user_mbi': '1SA0A00AA00',
                    'user_hicn_hash': '71f16b70b1b4fbdad76b',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': 'Hello',
                    'last_name': 'World',
                    'email': 'oscar@sesamestreet.gov',
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'incorrect user HICN hash format',
            },
            # try to create a record with a len(user_mbi) > 11
            'invalid_mbi_too_long': {
                'args': {
                    'username': '00112233-4455-6677-8899-aabbccddeeff',
                    'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                    'mbi': '1SA0A00AA00000',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': 'Hello',
                    'last_name': 'World',
                    'email': 'oscar@sesamestreet.gov',
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'incorrect user MBI format',
            },
            'empty string mbi': {
                'args': {
                    'username': '00112233-4455-6677-8899-aabbccddeeff',
                    'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                    'mbi': '',
                    'fhir_id_v2': '-20140000008325',
                    'user_id_type': 'H',
                    'first_name': 'Hello',
                    'last_name': 'World',
                    'email': 'oscar@sesamestreet.gov',
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'incorrect user MBI format',
            },
            'empty_fhir_id_v2': {
                'args': {
                    'username': '00112233-4455-6677-8899-aabbccddeeff',
                    'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                    'fhir_id_v2': '',
                    'user_id_type': 'H',
                    'first_name': 'Hello',
                    'last_name': 'World',
                    'email': 'oscar@sesamestreet.gov',
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'fhir_id_v2 can not be an empty string',
            },
            'empty_fhir_id_v3': {
                'args': {
                    'username': '00112233-4455-6677-8899-aabbccddeeff',
                    'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                    'fhir_id_v3': '',
                    'user_id_type': 'H',
                    'first_name': 'Hello',
                    'last_name': 'World',
                    'email': 'oscar@sesamestreet.gov',
                },
                'exception': BBMyMedicareCallbackCrosswalkCreateException,
                'exception_mesg': 'fhir_id_v3 can not be an empty string',
            },
            'no_fhir_id': {
                'args': {
                    'username': '00112233-4455-6677-8899-aabbccddeeff',
                    'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                    'user_id_type': 'H',
                    'first_name': 'Hello',
                    'last_name': 'World',
                    'email': 'oscar@sesamestreet.gov',
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
                        'username': '00112233-4455-6677-8899-aabbccddeeff',
                        'user_hicn_hash': '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
                        'user_id_type': 'H',
                        'fhir_id_v2': '-19990000000001',
                    },
                    {
                        'username': '00112233-4455-6677-8899-aabbccddeeff',
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
                                                                    success=True,
                                                                    fhir_id='-20000000002346',
                                                                    lookup_type=MatchFhirIdLookupType.MBI)))
    @patch('apps.fhir.bluebutton.models.ArchivedCrosswalk.create')
    def test_user_mbi_updated_from_null(self, mock_archive, mock_match_fhir) -> None:
        """Test that user_mbi gets updated when previously null"""
        fake_user = User.objects.create_user(
            username='00112233-4455-6677-8899-aabbccddeeff',
            email='oscar@sesamestreet.gov'
        )
        slsx_mbi = '1S00EU7JH82'

        crosswalk = Crosswalk.objects.create(
            user=fake_user,
            fhir_id_v2='-20000000002346',
            user_hicn_hash='50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
            user_mbi=None,
            user_id_type='M'
        )

        slsx_client = Mock(spec=OAuth2ConfigSLSx)
        slsx_client.user_id = '00112233-4455-6677-8899-aabbccddeeff'
        slsx_client.mbi = slsx_mbi
        slsx_client.hicn_hash = '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b'

        user, crosswalk_type = get_and_update_user(slsx_client, mock_request)

        user.refresh_from_db()
        crosswalk.refresh_from_db()
        self.assertEqual(user.crosswalk.user_mbi, slsx_mbi)
        mock_archive.assert_called_once()

    @patch('apps.mymedicare_cb.models.match_fhir_id', return_value=(MatchFhirIdResult(
                                                                    success=True,
                                                                    fhir_id='-20000000002346',
                                                                    lookup_type=MatchFhirIdLookupType.MBI)))
    @patch('apps.fhir.bluebutton.models.ArchivedCrosswalk.create')
    def test_user_mbi_updated_from_different_value(self, mock_archive, mock_match_fhir) -> None:
        """Test that user_mbi gets updated when previously a different value"""
        fake_user = User.objects.create_user(
            username='00112233-4455-6677-8899-aabbccddeeff',
            email='oscar@sesamestreet.gov'
        )
        slsx_mbi = '1S00EU7JH82'

        crosswalk = Crosswalk.objects.create(
            user=fake_user,
            fhir_id_v2='-20000000002346',
            user_hicn_hash='50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b',
            user_mbi='1S00EU7JH00',
            user_id_type='M'
        )

        slsx_client = Mock(spec=OAuth2ConfigSLSx)
        slsx_client.user_id = '00112233-4455-6677-8899-aabbccddeeff'
        slsx_client.mbi = slsx_mbi
        slsx_client.hicn_hash = '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b'

        user, crosswalk_type = get_and_update_user(slsx_client, mock_request)

        user.refresh_from_db()
        crosswalk.refresh_from_db()
        self.assertEqual(user.crosswalk.user_mbi, slsx_mbi)
        mock_archive.assert_called_once()
