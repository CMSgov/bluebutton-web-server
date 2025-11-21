import os
from .selenium_generic import SeleniumGenericTests
from .selenium_cases import TESTS
from apps.versions import Versions


USE_NEW_PERM_SCREEN = os.environ['USE_NEW_PERM_SCREEN']


class TestBlueButtonAPI(SeleniumGenericTests):
    '''
    Test authorization and fhir flow through the built in testclient by
    leveraging selenium web driver (chrome is used)
    '''
    def test_auth_grant_pkce_fhir_calls_v2(self):
        step = [0]
        test_name = "auth_grant_pkce_fhir_calls"
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    def test_auth_deny_fhir_calls_v2(self):
        step = [0]
        test_name = "auth_deny_fhir_calls"
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    def test_auth_grant_w_no_demo_v2(self):
        step = [0]
        if USE_NEW_PERM_SCREEN == "true":
            test_name = "auth_grant_w_no_demo_new_perm_screen"
        else:
            test_name = "auth_grant_w_no_demo"
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    '''
    Test lang param support on the authorize end point via the built in
    testclient using the Selenium web driver (Chrome)
    direct to login url with lang=en by click on "Authorize as beneficiary" button
    '''
    def test_authorize_lang_english_button(self):
        step = [0]
        test_name = "authorize_lang_english_button"
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        if USE_NEW_PERM_SCREEN == "true":
            # the validation of expire date etc. only applicable to new perm screen
            self._play(TESTS[test_name], step, api_ver=api_ver)
        else:
            print("Skip test " + test_name + " - only for new perm screen.")
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    '''
    Test authorizing through the test client, using v2 URLs, and ensuring all of the
    SMART App v2 Scopes are available within the returned token
    '''
    def test_v2_authorization_and_scopes(self):
        step = [0]
        test_name = "authorize_get_v2_scopes"
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)

        self._play(TESTS[test_name], step, api_ver=api_ver)

        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)
