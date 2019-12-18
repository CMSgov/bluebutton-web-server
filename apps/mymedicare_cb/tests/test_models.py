from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from ..models import create_beneficiary_record


class BeneficiaryLoginTest(TestCase):

    def setUp(self):
        Group.objects.create(name='BlueButton')

    def test_create_beneficiary_record(self):
        args = {
            "username": "worldhello",
            "user_id_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
            "fhir_id": "-20000000002346",
            "first_name": "Hello",
            "last_name": "World",
            "email": "fu@bar.bar",
        }
        bene = create_beneficiary_record(**args)
        self.assertTrue(bene.pk > 0)  # asserts that it was saved to the db
        self.assertEqual(bene.username, args["username"])
        self.assertEqual(bene.crosswalk.user_id_hash, args["user_id_hash"])
        self.assertEqual(bene.crosswalk.fhir_id, args["fhir_id"])
        self.assertEqual(bene.userprofile.user_type, 'BEN')

    def test_fail_create_beneficiary_record(self):
        cases = {
            "missing username": {
                "args": {
                    "user_id_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    "first_name": "Hello",
                    "last_name": "World",
                    "email": "fu@bar.bar",
                },
                "exception": AssertionError,
            },
            "missing hash": {
                "args": {
                    "username": "helloworld",
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
                        "username": "test01",
                        "user_id_hash": "50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    },
                    {
                        "username": "test01",
                        "user_id_hash": "60ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    },
                ],
                "exception": ValidationError,
            },
            "colliding hash": {
                "args": [
                    {
                        "username": "test02",
                        "user_id_hash": "70ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    },
                    {
                        "username": "test03",
                        "user_id_hash": "70ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                    },
                ],
                "exception": ValidationError,
            },
            "colliding fhir_id": {
                "args": [
                    {
                        "username": "test04",
                        "user_id_hash": "80ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "fhir_id": 12345,
                    },
                    {
                        "username": "test05",
                        "user_id_hash": "90ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b",
                        "fhir_id": 12345,
                    },
                ],
                "exception": ValidationError,
            },
        }
        for name, case in cases.items():
            create_beneficiary_record(**case["args"][0])
            with self.assertRaises(case["exception"], msg=name):
                create_beneficiary_record(**case["args"][1])
