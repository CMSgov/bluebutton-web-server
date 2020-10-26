import uuid

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.fhir.bluebutton.models import BBFhirBluebuttonModelException
from apps.test import BaseApiTest
from ..models import Crosswalk, check_crosswalks, hash_hicn, hash_mbi


class TestModels(BaseApiTest):

    def test_crosswalk_setter_properties(self):
        '''
          Test the Crosswalk setters
          and that they can not be modified once set.
        '''
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net',
                                 fhir_id="-20000000000001",
                                 user_hicn_hash=self.test_hicn_hash,
                                 user_mbi_hash=self.test_mbi_hash)

        cw = Crosswalk.objects.get(user=user)

        with self.assertRaisesRegexp(ValidationError, "this value cannot be modified."):
            cw.fhir_id = "-20000000000002"

        with self.assertRaisesRegexp(ValidationError, "this value cannot be modified."):
            cw.user_hicn_hash = uuid.uuid4()

        with self.assertRaisesRegexp(ValidationError, "this value cannot be modified."):
            cw.user_mbi_hash = uuid.uuid4()

    def test_require_fhir_id(self):
        with self.assertRaisesRegexp(IntegrityError, "[NOT NULL constraint|null value in column].*fhir_id.*"):
            self._create_user('john', 'password',
                              first_name='John',
                              last_name='Smith',
                              email='john@smith.net',
                              fhir_id=None)

    def test_require_user_hicn_hash(self):
        # NOTE: The user_hicn_hash's DB field name is still user_id_hash in regex below.
        with self.assertRaisesRegexp(IntegrityError, "[NOT NULL constraint|null value in column].*user_id_hash.*"):
            self._create_user('john', 'password',
                              first_name='John',
                              last_name='Smith',
                              email='john@smith.net',
                              fhir_id="-20000000000001",
                              user_hicn_hash=None)

    def test_not_require_user_mbi_hash(self):
        '''
            user_mbi_hash can be null for backward compatability
            and also an empty string return value from SLS.
        '''
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net',
                                 fhir_id="-20000000000001",
                                 user_hicn_hash=self.test_hicn_hash,
                                 user_mbi_hash=None)

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_mbi_hash, None)

    def test_immutable_fhir_id(self):
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')

        cw = Crosswalk.objects.get(user=user)
        with self.assertRaises(ValidationError):
            cw.fhir_id = "-20000000000002"

    def test_immuatble_user_hicn_hash(self):
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_hicn_hash, self.test_hicn_hash)
        with self.assertRaises(ValidationError):
            cw.user_hicn_hash = "239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130"

    def test_immuatble_user_mbi_hash(self):
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net')

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_mbi_hash, self.test_mbi_hash)
        with self.assertRaises(ValidationError):
            cw.user_mbi_hash = "239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130"

    def test_mutable_user_mbi_hash_when_null(self):
        '''
            Test replacing Null mbi_hash value in crosswalk.
            Unlike hich_hash, this case is OK if past value was Null/None.
        '''
        user = self._create_user('john', 'password',
                                 first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net',
                                 user_mbi_hash=None)

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_mbi_hash, None)

        cw.user_mbi_hash = "239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130"
        cw.save()

        cw = Crosswalk.objects.get(user=user)
        self.assertEqual(cw.user_mbi_hash, "239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130")

    def test_crosswalk_real_synth_query_managers(self):
        '''
            Test the RealCrosswalkManager and SynthCrosswalkManager queryset managers using
            the check_crosswalks method.
        '''

        # Create 5x Real (positive FHIR_ID) users
        for cnt in range(5):
            self._create_user('johnsmith' + str(cnt), 'password',
                              first_name='John1' + str(cnt),
                              last_name='Smith',
                              email='john' + str(cnt) + '@smith.net',
                              fhir_id='2000000000000' + str(cnt),
                              user_hicn_hash='239e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt),
                              user_mbi_hash='9876543217ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt))

        # Create 7x Synthetic (negative FHIR_ID) users
        for cnt in range(7):
            self._create_user('johndoe' + str(cnt), 'password',
                              first_name='John1' + str(cnt),
                              last_name='Doe',
                              email='john' + str(cnt) + '@doe.net',
                              fhir_id='-2000000000000' + str(cnt),
                              user_hicn_hash='255e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt),
                              user_mbi_hash='987654321aaaa11111aaaa195a47a82a2cd6f46e911660fe9775f6e00000000' + str(cnt))

        self.assertEqual("{'synthetic': 7, 'real': 5}", str(check_crosswalks()))

    def test_hash_hicn_empty_string(self):
        '''
            BB2-237: Test the hash_hicn(hicn) function for empty string produces exception instead of assert
        '''
        # Test non-empty value first
        hash_hicn("1234567890A")

        # Test empty value
        with self.assertRaisesRegexp(BBFhirBluebuttonModelException, "HICN cannot be the empty string.*"):
            hash_hicn("")

    def test_hash_mbi_empty_string(self):
        '''
            BB2-237: Test the hash_mbi(mbi) function for empty string produces exception instead of assert
        '''
        # Test non-empty value first
        hash_mbi("1SA0A00AA00")

        # Test empty value
        with self.assertRaisesRegexp(BBFhirBluebuttonModelException, "MBI cannot be the empty string.*"):
            hash_mbi("")
