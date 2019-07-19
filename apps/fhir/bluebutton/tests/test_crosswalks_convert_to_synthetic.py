from apps.test import BaseApiTest

from ..models import Crosswalk, check_crosswalks, convert_crosswalks_to_synthetic
from ...server.models import ResourceRouter


class TestCrosswalkConvertSynthetic(BaseApiTest):
    def create_test_crosswalks(self, fhir_id_type, start, end):

        for user_num in range(start, end):
            # Create a user
            user = self._create_user(fhir_id_type + str(user_num), 'password',
                                     first_name='John',
                                     last_name='Last' + str(user_num),
                                     email='johnlast' + str(user_num) + '@smith.net')

            # created a default resource router
            fs = ResourceRouter.objects.create(name="Main Server",
                                               fhir_url="http://localhost:8000/fhir/",
                                               shard_by="Patient",
                                               server_search_expiry=1800)

            if fhir_id_type == 'positive':
                fhir_id = "20000000000000" + str(user_num)
            elif fhir_id_type == 'negative':
                fhir_id = "-20000000000000" + str(user_num)
            else:
                fhir_id = ""

            Crosswalk.objects.create(user=user,
                                     fhir_source=fs,
                                     fhir_id=fhir_id)

    def test_crosswalks_convert_to_synth(self):
        '''
            Test crosswalk conversions with 9x total crosswalks of different types.
        '''
        #   Create 4x real/positive FHIR_ID users/crosswalks
        self.create_test_crosswalks('positive', 1, 5)
        #   Create 3x synth/negative FHIR_ID users/crosswalks
        self.create_test_crosswalks('negative', 6, 9)
        #   Create 2x blank FHIR_ID="" users/crosswalks
        self.create_test_crosswalks('blank', 10, 12)

        ret = check_crosswalks()
        # Verify BEFORE SYNTH count == 3:
        self.assertEqual(ret['synthetic'], 3)
        # Verify BEFORE REAL count == 4:
        self.assertEqual(ret['real'], 4)
        # Verify BEFORE BLANK count == 2:
        blank_count = Crosswalk.objects.filter(fhir_id='').count()
        self.assertEqual(blank_count, 2)
        # Verify BEFORE total count == 9:
        total_count = Crosswalk.objects.all().count()
        self.assertEqual(total_count, 9)

        '''
             Test that the conversion DOES NOT WORK when the allowed FHIR server url
             hash does not match the target FHIR server.
        '''
        convert_crosswalks_to_synthetic("INVALID-ALLOWED-FHIR-URL-HASH")

        ret = check_crosswalks()
        # Verify no change SYNTH count == 3:
        self.assertEqual(ret['synthetic'], 3)
        # Verify no change REAL count == 4:
        self.assertEqual(ret['real'], 4)
        # Verify no change BLANK count == 2:
        blank_count = Crosswalk.objects.filter(fhir_id='').count()
        self.assertEqual(blank_count, 2)
        # Verify no change total count == 9:
        total_count = Crosswalk.objects.all().count()
        self.assertEqual(total_count, 9)

        '''
            Test that the conversion DOES WORK when the allowed FHIR server url
            hash IS VALID for fhir_url="http://localhost:8000/fhir/",
        '''
        convert_crosswalks_to_synthetic("79f330b587728a2a607775e713161fd3b31d306091350c957e1ef4b71231ccec")

        ret = check_crosswalks()
        # Verify AFTER SYNTH count == 7:
        self.assertEqual(ret['synthetic'], 7)
        # Verify AFTER REAL count == 0:
        self.assertEqual(ret['real'], 0)
        # Verify AFTER BLANK count == 2:
        blank_count = Crosswalk.objects.filter(fhir_id='').count()
        self.assertEqual(blank_count, 2)
        # Verify AFTER total count == 9.:
        total_count = Crosswalk.objects.all().count()
        self.assertEqual(total_count, 9)
