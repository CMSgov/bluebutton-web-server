from apps.integration_tests.common_utils import screenshot_on_exception
from apps.integration_tests.constants import TESTS, USE_NEW_PERM_SCREEN
from apps.integration_tests.selenium_generic import SeleniumGenericTests
from apps.versions import Versions


class TestBlueButtonAPI(SeleniumGenericTests):
    """Test authorization and fhir flow through the built in testclient by
        leveraging selenium web driver (chrome is used)

    Args:
        SeleniumGenericTests (class): base selenium test class, runs via pytest
    """

    @screenshot_on_exception
    def test_auth_grant_fhir_calls_v2(self):
        """
        Test authorizing through the test client, using v2 URLs, and ensuring all of the
        FHIR resources are returned (ie. the EOB, Patient, Coverage, and ExplanationOfBenefit resources)
        """
        step = [0]
        test_name = 'auth_grant_fhir_calls_v2'
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    @screenshot_on_exception
    def test_auth_grant_fhir_calls_v3(self):
        """
        Test authorizing through the test client, using v3 URLs, and ensuring all of the
        FHIR resources are returned (ie. the EOB, Patient, Coverage, and ExplanationOfBenefit resources)
        """
        step = [0]
        test_name = 'auth_grant_fhir_calls_v3'
        api_ver = Versions.V3
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    @screenshot_on_exception
    def test_auth_deny_fhir_calls_v2(self):
        """
        Test denying authorization through the test client, using v2 URLs, and ensuring all of the
        FHIR resources are NOT returned (ie. the EOB, Patient, Coverage, and ExplanationOfBenefit resources)
        """
        step = [0]
        test_name = 'auth_deny_fhir_calls_v2'
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    @screenshot_on_exception
    def test_auth_grant_w_no_demo_v2(self):
        """
        Test authorizing through the test client, using v2 URLs, and ensuring all of the
        FHIR resources are returned (ie. the EOB, Patient, Coverage, and ExplanationOfBenefit resources)
        when the user has NOT chosen to share their demographic data in the system
        """
        step = [0]
        if USE_NEW_PERM_SCREEN == 'true':
            test_name = 'auth_grant_w_no_demo_new_perm_screen'
        else:
            test_name = 'auth_grant_w_no_demo_v2'
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    @screenshot_on_exception
    def test_authorize_lang_english_button(self):
        """
        Test lang param support on the authorize end point via the built in
        testclient using the Selenium web driver (Chrome)
        direct to login url with lang=en by click on "Authorize as beneficiary" button
        """
        step = [0]
        test_name = 'authorize_lang_english_button'
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        if USE_NEW_PERM_SCREEN == 'true':
            # the validation of expire date etc. only applicable to new perm screen
            self._play(TESTS[test_name], step, api_ver=api_ver)
        else:
            print('Skip test ' + test_name + ' - only for new perm screen.')
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    @screenshot_on_exception
    def test_v2_authorization_and_scopes(self):
        """
        Test authorizing through the test client, using v2 URLs, and ensuring all of the
        SMART App v2 Scopes are available within the returned token
        """
        step = [0]
        test_name = 'authorize_get_v2_scopes'
        api_ver = Versions.V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)

        self._play(TESTS[test_name], step, api_ver=api_ver)

        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    @screenshot_on_exception
    def test_samhsa_box_checked_eob_response_v3(self):
        """
        Test that the samhsa checkbox is checked and that
        _security%3Anot=42CFRPart2 is NOT part of the EOB
        url response since we aren't filtering out any SAMHSA data.
        """
        step = [0]
        test_name = 'samhsa_box_checked_eob_response_v3'
        api_ver = Versions.V3
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    @screenshot_on_exception
    def test_samhsa_box_not_checked_eob_response_v3(self):
        """
        Test that the samhsa checkbox is NOT checked and that
        _security%3Anot=42CFRPart2 IS part of the EOB url response
        since we are filtering out SAMHSA data.
        """
        step = [0]
        test_name = 'samhsa_box_not_checked_eob_response_v3'
        api_ver = Versions.V3
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)
