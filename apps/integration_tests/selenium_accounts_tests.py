from .selenium_generic import SeleniumGenericTests
from .selenium_cases import (
    USER_ACCT_ACTIVATION_EMAIL_SUBJ,
    USER_ACCT_ACTIVATION_KEY_PREFIX,
    USER_ACTIVATION_URL_FMT,
    ACCT_TESTS,
)


class SeleniumUserAndAppTests(SeleniumGenericTests):

    def testAccountAndAppMgmt(self):
        step = [0]
        test_name = "create_user_account"
        api_ver = "*"
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(ACCT_TESTS[test_name], step, api_ver=api_ver)
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)
        step = [0]
        # activate request with a faked key should give expected error message with an email
        # for further assistance
        test_name = "validate_activation_key_err_msg"
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(ACCT_TESTS[test_name], step, api_ver=api_ver)
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)
        # now activate the user account
        activation_key = self._validate_events(USER_ACCT_ACTIVATION_EMAIL_SUBJ, USER_ACCT_ACTIVATION_KEY_PREFIX)
        # good activation requests are idempotent - should not generate any extra email notifications
        # activate once
        self._load_page(USER_ACTIVATION_URL_FMT.format(activation_key))
        # activate twice
        self._load_page(USER_ACTIVATION_URL_FMT.format(activation_key))
        # there is still one activation email
        activation_key = self._validate_events(USER_ACCT_ACTIVATION_EMAIL_SUBJ, USER_ACCT_ACTIVATION_KEY_PREFIX)
        # now login to the account and do app stuff
        step = [0]
        test_name = "login_user_account_add_app"
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(ACCT_TESTS[test_name], step, api_ver=api_ver)
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)
        # step = [0]
        # test_name = "validate_1st_api_call_email"
        # self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        # self._play(ACCT_TESTS[test_name], step, api_ver=api_ver)
        # self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)
