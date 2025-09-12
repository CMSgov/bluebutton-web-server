from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group

from apps.fhir.bluebutton.models import Crosswalk
from apps.mymedicare_cb.models import BBMyMedicareCallbackCrosswalkCreateException
from apps.mymedicare_cb.authorization import OAuth2ConfigSLSx

from ..models import create_beneficiary_record, get_and_update_user
from unittest.mock import patch, Mock


class BeneficiaryLoginTest(TestCase):

    def setUp(self):
        Group.objects.create(name='BlueButton')

    def test_create_beneficiary_record(self):
        args = {
            "username": "00112233-4455-6677-8899-aabbccddeeff",
            "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            "user_mbi_hash": "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            "user_id_type": "H",
            "fhir_id": "-20000000002346",
            "first_name": "Hello",
            "last_name": "World",
            "email": "fu@bar.bar",
        }
        slsx_client = OAuth2ConfigSLSx(args)
        bene = create_beneficiary_record(slsx_client, args["fhir_id"])
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args["username"])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args["user_hicn_hash"])
        self.assertEqual(bene.crosswalk.user_mbi_hash, args["user_mbi_hash"])
        self.assertEqual(bene.crosswalk.user_id_type, args["user_id_type"])
        self.assertEqual(bene.crosswalk.fhir_id, args["fhir_id"])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_create_beneficiary_record_null_mbi_hash(self):
        # Test creating new record with a None (Null) user_mbi_hash value
        # This is OK. Handles the case where SLSx returns an empty mbi value.
        args = {
            "username": "00112233-4455-6677-8899-aabbccddeeff",
            "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            "user_mbi_hash": None,
            "user_id_type": "H",
            "fhir_id": "-20000000002346",
            "first_name": "Hello",
            "last_name": "World",
            "email": "fu@bar.bar",
        }
        slsx_client = OAuth2ConfigSLSx(args)
        bene = create_beneficiary_record(slsx_client, args["fhir_id"])
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args["username"])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args["user_hicn_hash"])
        self.assertEqual(bene.crosswalk.user_mbi_hash, args["user_mbi_hash"])
        self.assertEqual(bene.crosswalk.user_id_type, args["user_id_type"])
        self.assertEqual(bene.crosswalk.fhir_id, args["fhir_id"])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_create_beneficiary_record_no_mbi_hash(self):
        # Test creating new record with NO user_mbi_hash value
        # This is OK. Handles the case where SLSx returns an empty mbi value.
        args = {
            "username": "00112233-4455-6677-8899-aabbccddeeff",
            "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            "user_id_type": "H",
            "fhir_id": "-20000000002346",
            "first_name": "Hello",
            "last_name": "World",
            "email": "fu@bar.bar",
        }
        slsx_client = OAuth2ConfigSLSx(args)
        bene = create_beneficiary_record(slsx_client, args["fhir_id"])
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args["username"])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args["user_hicn_hash"])
        self.assertEqual(bene.crosswalk.user_mbi_hash, None)
        self.assertEqual(bene.crosswalk.user_id_type, args["user_id_type"])
        self.assertEqual(bene.crosswalk.fhir_id, args["fhir_id"])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_fail_create_beneficiary_record(self):
        cases = {
            "empty username": {
                "args": {
                    "username": "",
                    "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_mbi_hash": "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "fhir_id": "-20140000008325",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": BBMyMedicareCallbackCrosswalkCreateException,
                "exception_mesg": "username can not be None or empty string",
            },
            "missing username": {
                "args": {
                    "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_mbi_hash": "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "fhir_id": "-20140000008325",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": BBMyMedicareCallbackCrosswalkCreateException,
                "exception_mesg": "username can not be None",
            },
            "missing hash": {
                "args": {
                    "username": "00112233-4455-6677-8899-aabbccddeeff",
                    "user_mbi_hash": "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "fhir_id": "-20140000008325",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": BBMyMedicareCallbackCrosswalkCreateException,
                "exception_mesg": "user_hicn_hash can not be None",
            },
            "invalid_hicn_hash": {
                "args": {
                    "username": "00112233-4455-6677-8899-aabbccddeeff",
                    "user_mbi_hash": "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_hicn_hash": "71f16b70b1b4fbdad76b",
                    "fhir_id": "-20140000008325",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": BBMyMedicareCallbackCrosswalkCreateException,
                "exception_mesg": "incorrect user HICN hash format",
            },
            "invalid_mbi_hash": {
                "args": {
                    "username": "00112233-4455-6677-8899-aabbccddeeff",
                    "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_mbi_hash": "71f16b70b1b4fbdad76b",
                    "fhir_id": "-20140000008325",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": BBMyMedicareCallbackCrosswalkCreateException,
                "exception_mesg": "incorrect user MBI hash format",
            },

            "empty string mbi_hash": {
                "args": {
                    "username": "00112233-4455-6677-8899-aabbccddeeff",
                    "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_mbi_hash": "",
                    "fhir_id": "-20140000008325",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": BBMyMedicareCallbackCrosswalkCreateException,
                "exception_mesg": "incorrect user MBI hash format",
            },
            "missing_fhir_id": {
                "args": {
                    "username": "00112233-4455-6677-8899-aabbccddeeff",
                    "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_mbi_hash": "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": BBMyMedicareCallbackCrosswalkCreateException,
                "exception_mesg": "fhir_id can not be None",
            },
            "empty_fhir_id": {
                "args": {
                    "username": "00112233-4455-6677-8899-aabbccddeeff",
                    "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_mbi_hash": "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "fhir_id": "",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": BBMyMedicareCallbackCrosswalkCreateException,
                "exception_mesg": "fhir_id can not be an empty string",
            },
        }
        for name, case in cases.items():
            slsx_client = OAuth2ConfigSLSx(case["args"])
            with self.assertRaisesRegex(case["exception"], case["exception_mesg"]):
                create_beneficiary_record(slsx_client, case["args"].get("fhir_id", None))

    def test_fail_create_multiple_beneficiary_record(self):
        cases = {
            "colliding username": {
                "args": [
                    {
                        "username": "00112233-4455-6677-8899-aabbccddeeff",
                        "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_mbi_hash": "50a654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_id_type": "H",
                        "fhir_id": "-19990000000001",
                    },
                    {
                        "username": "00112233-4455-6677-8899-aabbccddeeff",
                        "user_hicn_hash": "60ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_mbi_hash": "60a654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_id_type": "H",
                        "fhir_id": "-19990000000002",
                    },
                ],
                "exception": ValidationError,
                "exception_mesg": "user already exists",
            },
            "colliding hicn_hash": {
                "args": [
                    {
                        "username": "10112233-4455-6677-8899-aabbccddeeff",
                        "user_hicn_hash": "70ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_mbi_hash": "70a654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_id_type": "H",
                        "fhir_id": "-19990000000003",
                    },
                    {
                        "username": "20112233-4455-6677-8899-aabbccddeeff",
                        "user_hicn_hash": "70ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_mbi_hash": "70b654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_id_type": "H",
                        "fhir_id": "-19990000000004",
                    },
                ],
                "exception": ValidationError,
                "exception_mesg": "user_hicn_hash already exists",
            },
            "colliding mbi_hash": {
                "args": [
                    {
                        "username": "60112233-4455-6677-8899-aabbccddeeff",
                        "user_hicn_hash": "a0ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_mbi_hash": "a0a654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_id_type": "H",
                        "fhir_id": "-19990000000006",
                    },
                    {
                        "username": "70112233-4455-6677-8899-aabbccddeeff",
                        "user_hicn_hash": "a0bd63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_mbi_hash": "a0a654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_id_type": "H",
                        "fhir_id": "-19990000000007",
                    },
                ],
                "exception": ValidationError,
                "exception_mesg": "user_mbi_hash already exists",
            },
            "colliding fhir_id": {
                "args": [
                    {
                        "username": "30112233-4455-6677-8899-aabbccddeeff",
                        "user_hicn_hash": "80ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_mbi_hash": "80a654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "fhir_id": "-19990000000005",
                    },
                    {
                        "username": "40112233-4455-6677-8899-aabbccddeeff",
                        "user_hicn_hash": "90ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "user_mbi_hash": "90a654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "fhir_id": "-19990000000005",
                    },
                ],
                "exception": ValidationError,
                "exception_mesg": "fhir_id already exists",
            },
        }

        for name, case in cases.items():
            arg0 = case["args"][0]
            slsx_client0 = OAuth2ConfigSLSx(case["args"][0])
            create_beneficiary_record(slsx_client0, arg0["fhir_id"])
            with self.assertRaisesRegex(case["exception"], case["exception_mesg"]):
                arg1 = case["args"][1]
                slsx_client1 = OAuth2ConfigSLSx(arg1)
                create_beneficiary_record(slsx_client1, arg1["fhir_id"])

    @patch("apps.mymedicare_cb.models.match_fhir_id", return_value=("-20000000002346", "M"))
    @patch("apps.fhir.bluebutton.models.ArchivedCrosswalk.create")
    def test_user_mbi_updated_from_null(self, mock_archive, mock_match_fhir) -> None:
        """Test that user_mbi gets updated when previously null"""
        fake_user = User.objects.create_user(
            username="00112233-4455-6677-8899-aabbccddeeff",
            email="fu@bar.bar"
        )
        slsx_mbi = "1S00EU7JH82"

        crosswalk = Crosswalk.objects.create(
            user=fake_user,
            fhir_id="-20000000002346",
            user_hicn_hash="50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            user_mbi_hash="987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            user_mbi=None,
            user_id_type="M"
        )

        slsx_client = Mock(spec=OAuth2ConfigSLSx)
        slsx_client.user_id = "00112233-4455-6677-8899-aabbccddeeff"
        slsx_client.mbi = slsx_mbi
        slsx_client.mbi_hash = "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"
        slsx_client.hicn_hash = "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"

        user, crosswalk_type = get_and_update_user(slsx_client)

        user.refresh_from_db()
        crosswalk.refresh_from_db()
        self.assertEqual(user.crosswalk.user_mbi, slsx_mbi)
        mock_archive.assert_called_once()

    @patch("apps.mymedicare_cb.models.match_fhir_id", return_value=("-20000000002346", "M"))
    @patch("apps.fhir.bluebutton.models.ArchivedCrosswalk.create")
    def test_user_mbi_updated_from_different_value(self, mock_archive, mock_match_fhir) -> None:
        """Test that user_mbi gets updated when previously null"""
        fake_user = User.objects.create_user(
            username='00112233-4455-6677-8899-aabbccddeeff',
            email="fu@bar.bar"
        )
        slsx_mbi = "1S00EU7JH82"

        crosswalk = Crosswalk.objects.create(
            user=fake_user,
            fhir_id="-20000000002346",
            user_hicn_hash="50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            user_mbi_hash="987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            user_mbi="1S00EU7JH00",
            user_id_type="M"
        )

        slsx_client = Mock(spec=OAuth2ConfigSLSx)
        slsx_client.user_id = "00112233-4455-6677-8899-aabbccddeeff"
        slsx_client.mbi = slsx_mbi
        slsx_client.mbi_hash = "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"
        slsx_client.hicn_hash = "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"

        user, crosswalk_type = get_and_update_user(slsx_client)

        user.refresh_from_db()
        crosswalk.refresh_from_db()
        self.assertEqual(user.crosswalk.user_mbi, slsx_mbi)
        mock_archive.assert_called_once()
