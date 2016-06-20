from __future__ import unicode_literals
from __future__ import absolute_import

from apps.test import BaseApiTest

from ..models import FhirServer, Crosswalk


class TestModels(BaseApiTest):
    def test_get_full_url_good(self):
        # Create a user
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')
        # created a default user
        fs = FhirServer.objects.create(name="Main Server",
                                       fhir_url="http://localhost:8000/fhir/",
                                       shard_by="Patient")

        cw = Crosswalk.objects.create(user=user,
                                      fhir_source=fs,
                                      fhir_id="123456")

        fhir = Crosswalk.objects.get(user=user.pk)

        url_info = fhir.get_fhir_patient_url()

        expected_result = '{}{}/{}'.format(fs.fhir_url, fs.shard_by, cw.fhir_id)
        self.assertEqual(url_info, expected_result)

    def test_get_full_url_bad(self):
        # Create a user
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')

        # created a default user
        fs = FhirServer.objects.create(name="Main Server",
                                       fhir_url="http://localhost:8000/fhir/",
                                       shard_by="Patient")

        Crosswalk.objects.create(user=user,
                                 fhir_source=fs,
                                 fhir_id="123456")

        fhir = Crosswalk.objects.get(user=user.pk)

        url_info = fhir.get_fhir_patient_url()

        invalid_match = "http://localhost:8000/fhir/" + "Practitioner/123456"
        self.assertNotEqual(url_info, invalid_match)
