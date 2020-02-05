from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from apps.test import BaseApiTest

from ..models import Crosswalk
from ...server.models import ResourceRouter


class TestModels(BaseApiTest):
    def test_get_full_url_good(self):
        # Create a user
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')

        user.crosswalk.delete()
        # created a default user
        fs = ResourceRouter.objects.create(name="Main Server",
                                           fhir_url="http://localhost:8000/fhir/",
                                           shard_by="Patient",
                                           server_search_expiry=1800)

        user.crosswalk.fhir_source = fs
        user.crosswalk.save()

        fhir = Crosswalk.objects.get(user=user.pk)

        url_info = fhir.get_fhir_patient_url()

        expected_result = '{}{}/{}'.format(fs.fhir_url, fs.shard_by, fhir.fhir_id)
        self.assertEqual(url_info, expected_result)

    def test_get_full_url_bad(self):
        # Create a user
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')
        user.crosswalk.delete()

        # created a default user
        fs = ResourceRouter.objects.create(name="Main Server",
                                           fhir_url="http://localhost:8000/fhir/",
                                           shard_by="Patient",
                                           server_search_expiry=1800)

        user.crosswalk.fhir_source = fs
        user.crosswalk.save()

        fhir = Crosswalk.objects.get(user=user.pk)

        url_info = fhir.get_fhir_patient_url()

        invalid_match = "http://localhost:8000/fhir/" + "Practitioner/123456"
        self.assertNotEqual(url_info, invalid_match)

    def test_require_fhir_id(self):
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')
        with self.assertRaisesRegexp(IntegrityError, "fhir_id"):
            Crosswalk.objects.create(user=user, user_id_hash=self.test_hash)

    def test_require_user_id_hash(self):
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')
        with self.assertRaisesRegexp(IntegrityError, "user_id_hash"):
            Crosswalk.objects.create(user=user, fhir_id="-20000000000001")

    def test_immutable_fhir_id(self):
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')

        cw = Crosswalk.objects.get(user=user)
        with self.assertRaises(ValidationError):
            cw.fhir_id = "-20000000000002"

    def test_immuatble_user_id_hash(self):
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_id_hash, self.test_hash)
        with self.assertRaises(ValidationError):
            cw.user_id_hash = "239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130"
