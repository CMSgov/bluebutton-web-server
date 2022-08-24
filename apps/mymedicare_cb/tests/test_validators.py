from django.test import TestCase
from ..validators import is_mbi_format_valid, is_mbi_format_synthetic
from string import ascii_uppercase


class MymedicareCbValidatorsTest(TestCase):

    def check_is_mbi_format_valid(self, mbi, expected_return_value):
        sls_mbi_format_valid, sls_mbi_format_msg = is_mbi_format_valid(mbi)
        return [sls_mbi_format_valid, sls_mbi_format_msg] == expected_return_value

    def test_validator_is_mbi_format_valid(self):
        '''
            Test the is_mbi_format_valid(mbi) function.
        '''
        # Build type_C_set: C – Numeric 1 thru 9
        type_C_set = set()
        for c in range(1, 10):
            type_C_set.add(str(c))

        # Build type_N_set: N – Numeric 0 thru 9
        type_N_set = set()
        for c in range(0, 10):
            type_N_set.add(str(c))

        # Build type_A_set: A – Alphabetic Character (A...Z); Excluding (S, L, O, I, B, Z)
        exclude_chars_set = {'S', 'L', 'O', 'I', 'B', 'Z'}
        type_A_set = set(ascii_uppercase).difference(exclude_chars_set)

        # Build type_A_pos2_set: A – Alphabetic Character (A...Z); Excluding (L, O, I, B, Z)
        #     In position 2, the "S" denotes a synthetic MBI.
        type_A_pos2_set = type_A_set | {"S"}

        # Build type_AN_set: AN – Either A or N
        type_AN_set = type_A_set | type_N_set

        # Base valid MBI
        base_valid_mbi = "4S10A00AA00"

        # 1. Test empty
        mbi = ""
        expected_return_value = [False, "Invalid length = 0"]
        # Assert validation return matches expected values.
        self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))

        # 2. Test size > 11
        mbi = "4S10A00AA00Z"
        expected_return_value = [False, "Invalid length = 12"]
        # Assert validation return matches expected values.
        self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))

        # 3. Test base_valid MBI
        mbi = base_valid_mbi
        expected_return_value = [True, "Valid"]
        # Assert validation return matches expected values.
        self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))

        # 4. Test type_C MBI position
        test_position = 0
        #     Valid tests:
        expected_return_value = [True, "Valid"]
        for c in type_C_set:
            mbi = c + base_valid_mbi[1:12]
            # Assert validation return matches expected values.
            self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))
        #     Invalid tests using type_A_set:
        expected_return_value = [False, "Invalid char in pos = " + str(test_position)]
        for c in type_A_set | {'0'}:
            mbi = c + base_valid_mbi[1:12]
            # Assert validation return matches expected values.
            self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))

        # 5. Test type_N MBI in positions:
        test_positions = [3, 6, 9, 10]
        for test_position in test_positions:
            # Valid tests:
            expected_return_value = [True, "Valid"]
            for c in type_N_set:
                mbi = base_valid_mbi[0:test_position] + c + base_valid_mbi[test_position + 1:12]
                # Assert validation return matches expected values.
                self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))
            # Invalid tests using type_A_set:
            expected_return_value = [False, "Invalid char in pos = " + str(test_position)]
            for c in type_A_set:
                mbi = base_valid_mbi[0:test_position] + c + base_valid_mbi[test_position + 1:12]
                # Assert validation return matches expected values.
                self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))

        # 6. Test type_A MBI in positions:
        test_positions = [4, 7, 8]
        for test_position in test_positions:
            # Valid tests:
            expected_return_value = [True, "Valid"]
            for c in type_A_set:
                mbi = base_valid_mbi[0:test_position] + c + base_valid_mbi[test_position + 1:12]
                # Assert validation return matches expected values.
                self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))
            # Invalid tests using type_N_set and exclude_chars_set
            expected_return_value = [False, "Invalid char in pos = " + str(test_position)]
            for c in type_N_set | exclude_chars_set:
                mbi = base_valid_mbi[0:test_position] + c + base_valid_mbi[test_position + 1:12]
                # Assert validation return matches expected values.
                self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))

        # 7. Test type_A_pos2 MBI in positions:
        test_position = 1
        # Valid tests:
        expected_return_value = [True, "Valid"]
        for c in type_A_pos2_set:
            mbi = base_valid_mbi[0:test_position] + c + base_valid_mbi[test_position + 1:12]
            # Assert validation return matches expected values.
            self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))
        # Invalid tests using type_N_set and exclude_chars_set
        expected_return_value = [False, "Invalid char in pos = " + str(test_position)]
        for c in type_N_set | exclude_chars_set.difference({"S"}):
            mbi = base_valid_mbi[0:test_position] + c + base_valid_mbi[test_position + 1:12]
            # Assert validation return matches expected values.
            self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))

        # 8. Test type_AN MBI in positions:
        test_positions = [2, 5]
        for test_position in test_positions:
            # Valid tests:
            expected_return_value = [True, "Valid"]
            for c in type_AN_set:
                mbi = base_valid_mbi[0:test_position] + c + base_valid_mbi[test_position + 1:12]
                # Assert validation return matches expected values.
                self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))
            # Invalid tests using exclude_chars_set
            expected_return_value = [False, "Invalid char in pos = " + str(test_position)]
            for c in exclude_chars_set:
                mbi = base_valid_mbi[0:test_position] + c + base_valid_mbi[test_position + 1:12]
                # Assert validation return matches expected values.
                self.assertTrue(self.check_is_mbi_format_valid(mbi, expected_return_value))

    def test_validator_is_mbi_format_synthetic(self):
        '''
            Test the is_mbi_format_synthetic(mbi) function.
        '''
        # Test synthetic
        mbi = "4S10A00AA00"
        self.assertTrue(is_mbi_format_synthetic(mbi))

        # Test real
        mbi = "4T10A00AA00"
        self.assertFalse(is_mbi_format_synthetic(mbi))
