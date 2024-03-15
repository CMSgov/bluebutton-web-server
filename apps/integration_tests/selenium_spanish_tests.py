from .selenium_generic import SeleniumGenericTests
from .selenium_cases import (
    API_V2,
    SPANISH_TESTS
)
USE_NEW_PERM_SCREEN = "true"

'''
For running against an actual SlSx server (i.e. TEST, SBX),
not for the mock SLSx implementation

IMPORTANT NOTE: Assumes that the test client app on the BB2 server
that you are testing is a THIRTEEN_MONTH app and that the app user
has the limit_data_access flag ON. This test will fail unless these
conditions are met. Do not include as part of smoke tests until
limit_data_access flag is on for everyone and TestApp is THIRTEEN_MONTH
on all environments.
'''


class TestPermissionScreenSpanish(SeleniumGenericTests):
    '''
    Test Spanish permission screen flow through the built in testclient by
    leveraging selenium web driver (chrome is used)
    '''
    def test_toggle_language_and_date_format(self):
        step = [0]
        test_name = "toggle_language"
        api_ver = API_V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(SPANISH_TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    '''
    Test lang param support on the authorize end point via the built in
    testclient using the Selenium web driver (Chrome)
    '''
    def test_authorize_lang_param(self):
        step = [0]
        test_name = "authorize_lang_param"
        api_ver = API_V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(SPANISH_TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)
