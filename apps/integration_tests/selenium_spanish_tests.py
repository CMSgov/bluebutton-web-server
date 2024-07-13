from .selenium_generic import SeleniumGenericTests
from .selenium_cases import (
    API_V2,
    SPANISH_TESTS
)

USE_NEW_PERM_SCREEN = "true"

'''
For running against an actual SlSx server (i.e. TEST, SBX),
not for the mock SLSx implementation
'''


class TestPermissionScreenSpanish(SeleniumGenericTests):
    '''
    Test Spanish permission screen flow through the built in testclient by
    leveraging selenium web driver (chrome is used)
    '''
    # def test_toggle_language_and_date_format(self):
    #     step = [0]
    #     test_name = "toggle_language"
    #     api_ver = API_V2
    #     self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
    #     self._play(SPANISH_TESTS[test_name], step, api_ver=api_ver)
    #     self._testclient_home()
    #     self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    '''
    Test lang param support on the authorize end point via the built in
    testclient using the Selenium web driver (Chrome)
    inject lang=es before direct to login url
    '''
    # def test_authorize_lang_param(self):
    #     step = [0]
    #     test_name = "authorize_lang_param"
    #     api_ver = API_V2
    #     self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
    #     self._play(SPANISH_TESTS[test_name], step, api_ver=api_ver)
    #     self._testclient_home()
    #     self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    '''
    Test lang param support on the authorize end point via the built in
    testclient using the Selenium web driver (Chrome)
    direct to login url with lang=es by click on "Authorize as beneficiary (Spanish)" button
    '''
    def test_authorize_lang_spanish_button(self):
        step = [0]
        test_name = "authorize_lang_spanish_button"
        api_ver = API_V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        if USE_NEW_PERM_SCREEN == "true":
            # the validation of expire date etc. only applicable to new perm screen
            self._play(SPANISH_TESTS[test_name], step, api_ver=api_ver)
        else:
            print("Skip test " + test_name + " - only for new perm screen.")
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)
