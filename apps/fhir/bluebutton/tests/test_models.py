from django.db.utils import IntegrityError
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
            Crosswalk.objects.create(user=user)
