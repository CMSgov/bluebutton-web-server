from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from ..models import create_beneficiary_record


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
        bene = create_beneficiary_record(**args)
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args["username"])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args["user_hicn_hash"])
        self.assertEqual(bene.crosswalk.user_mbi_hash, args["user_mbi_hash"])
        self.assertEqual(bene.crosswalk.user_id_type, args["user_id_type"])
        self.assertEqual(bene.crosswalk.fhir_id, args["fhir_id"])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_create_beneficiary_record_null_mbi_hash(self):
        # Test creating new record with a None (Null) user_mbi_hash value
        # This is OK. Handles the case where SLS returns an empty mbi value.
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
        bene = create_beneficiary_record(**args)
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args["username"])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args["user_hicn_hash"])
        self.assertEqual(bene.crosswalk.user_mbi_hash, args["user_mbi_hash"])
        self.assertEqual(bene.crosswalk.user_id_type, args["user_id_type"])
        self.assertEqual(bene.crosswalk.fhir_id, args["fhir_id"])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_create_beneficiary_record_no_mbi_hash(self):
        # Test creating new record with NO user_mbi_hash value
        # This is OK. Handles the case where SLS returns an empty mbi value.
        args = {
            "username": "00112233-4455-6677-8899-aabbccddeeff",
            "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            "user_id_type": "H",
            "fhir_id": "-20000000002346",
            "first_name": "Hello",
            "last_name": "World",
            "email": "fu@bar.bar",
        }
        bene = create_beneficiary_record(**args)
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args["username"])
        self.assertEqual(bene.crosswalk.user_hicn_hash, args["user_hicn_hash"])
        self.assertEqual(bene.crosswalk.user_mbi_hash, None)
        self.assertEqual(bene.crosswalk.user_id_type, args["user_id_type"])
        self.assertEqual(bene.crosswalk.fhir_id, args["fhir_id"])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_fail_create_beneficiary_record(self):
        cases = {
            "missing username": {
                "args": {
                    "user_hicn_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_mbi_hash": "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": AssertionError,
            },
            "missing hash": {
                "args": {
                    "username": "00112233-4455-6677-8899-aabbccddeeff",
                    "user_mbi_hash": "987654321f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": AssertionError,
            },
            "empty string mbi_hash": {
                "args": {
                    "username": "00112233-4455-6677-8899-aabbccddeeff",
                    "user_mbi_hash": "",
                    "user_id_type": "H",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": AssertionError,
            },
        }
        for name, case in cases.items():
            with self.assertRaises(case["exception"]):
                create_beneficiary_record(**case["args"])

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
            },
        }
        for name, case in cases.items():
            create_beneficiary_record(**case["args"][0])
            with self.assertRaises(case["exception"], msg=name):
                create_beneficiary_record(**case["args"][1])
