from django.db.utils import IntegrityError

from apps.fhir.bluebutton.models import BBFhirBluebuttonModelException
from apps.test import BaseApiTest
from ..models import Crosswalk, get_crosswalk_bene_counts, hash_hicn


class TestModels(BaseApiTest):

    def test_require_user_hicn_hash(self):
        # NOTE: The user_hicn_hash's DB field name is still user_id_hash in regex below.
        with self.assertRaisesRegex(
            IntegrityError, "[NOT NULL constraint|null value in column].*user_id_hash.*"
        ):
            self._create_user(
                "john",
                "password",
                first_name="John",
                last_name="Smith",
                email="john@smith.net",
                fhir_id_v2="-20000000000001",
                user_hicn_hash=None,
            )

    def test_not_require_user_mbi(self):
        """
        user_mbi can be null for backward compatability
        and also an empty string return value from SLS.
        """
        user = self._create_user(
            "john",
            "password",
            first_name="John",
            last_name="Smith",
            email="john@smith.net",
            fhir_id_v2="-20000000000001",
            fhir_id_v3="-30000000000001",
            user_hicn_hash=self.test_hicn_hash,
            user_mbi=None,
        )

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_mbi, None)

    def test_mutable_fhir_id(self):
        user = self._create_user(
            "john",
            "password",
            first_name="John",
            last_name="Smith",
            email="john@smith.net",
            fhir_id_v2="-20000000000001",
            fhir_id_v3="-30000000000001",
        )
        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.fhir_id(2), "-20000000000001")
        self.assertEqual(cw.fhir_id(3), "-30000000000001")
        cw.set_fhir_id("-20000000000002", 2)
        cw.set_fhir_id("-30000000000002", 3)
        self.assertEqual(cw.fhir_id(2), "-20000000000002")
        self.assertEqual(cw.fhir_id(3), "-30000000000002")

    def test_mutable_user_hicn_hash(self):
        user = self._create_user(
            "john",
            "password",
            first_name="John",
            last_name="Smith",
            email="john@smith.net",
        )

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_hicn_hash, self.test_hicn_hash)
        cw.user_hicn_hash = (
            "239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130"
        )
        cw.save()

    def test_mutable_user_mbi(self):
        '''
        Ensure the user_mbi column on crosswalk can be updated
        '''
        user = self._create_user(
            "john",
            "password",
            first_name="John",
            last_name="Smith",
            email="john@smith.net",
        )

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_mbi, self.test_mbi)
        cw.user_mbi = '1SA0A00BB00'
        cw.save()

    def test_mutable_user_mbi_when_null(self):
        """
        Test replacing Null mbi value in crosswalk.
        Unlike hich_hash, this case is OK if past value was Null/None.
        """
        '''
        Ensure the user_mbi column on crosswalk can be updated
        even if the prior value was None
        '''
        user = self._create_user(
            "john",
            "password",
            first_name="John",
            last_name="Smith",
            email="john@smith.net",
            user_mbi=None,
        )

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_mbi, None)

        cw.user_mbi = (
            '1SA0A00CC00'
        )
        cw.save()

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(
            cw.user_mbi,
            '1SA0A00CC00',
        )

    def test_crosswalk_real_synth_query_managers(self):
        """
        Test the RealCrosswalkManager and SynthCrosswalkManager queryset managers using
        the get_crosswalk_bene_counts method.
        """

        # Create 5x Real (positive FHIR_ID) users
        for cnt in range(5):
            self._create_user(
                "johnsmith" + str(cnt),
                "password",
                first_name="John1" + str(cnt),
                last_name="Smith",
                email="john" + str(cnt) + "@smith.net",
                fhir_id_v2="2000000000000" + str(cnt),
                fhir_id_v3="3000000000000" + str(cnt),
                user_hicn_hash="239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000"
                + str(cnt),
                user_mbi=self._generate_random_mbi(),
            )

        # Create 7x Synthetic (negative FHIR_ID) users
        for cnt in range(7):
            self._create_user(
                "johndoe" + str(cnt),
                "password",
                first_name="John1" + str(cnt),
                last_name="Doe",
                email="john" + str(cnt) + "@doe.net",
                fhir_id_v2="-2000000000000" + str(cnt),
                fhir_id_v3="-3000000000000" + str(cnt),
                user_hicn_hash="255e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000"
                + str(cnt),
                user_mbi=self._generate_random_mbi(),
            )

        cc = get_crosswalk_bene_counts()
        self.assertEqual(cc["synthetic"], 7)
        self.assertEqual(cc["real"], 5)

    def test_hash_hicn_empty_string(self):
        """
        BB2-237: Test the hash_hicn(hicn) function for empty string produces exception instead of assert
        """
        # Test non-empty value first
        hash_hicn("1234567890A")

        # Test empty value
        with self.assertRaisesRegex(
            BBFhirBluebuttonModelException, "HICN cannot be the empty string.*"
        ):
            hash_hicn("")
