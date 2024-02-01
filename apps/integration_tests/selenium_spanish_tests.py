from .selenium_generic import SeleniumGenericTests
from .selenium_cases import (
    API_V2,
    SPANISH_TESTS
)
USE_NEW_PERM_SCREEN = "true"


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
