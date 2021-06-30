import os
import time
from django.conf import settings
from django.test import TestCase
from enum import Enum

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

TESTCLIENT_BUNDLE_LABEL_FMT = "Response (Bundle of {}), API version: {}"
TESTCLIENT_RESOURCE_LABEL_FMT = "Response ({}), API version: {}"
MESSAGE_NO_PERMISSION = "You do not have permission to perform this action."
TESTCASE_BANNER_FMT = "** {} TEST: {}, API: {}, STEP: {}, {}"
'''
UI Widget text: texts on e.g. buttons, links, labels etc.
'''
LNK_TXT_TESTCLIENT = "Test Client"
LNK_TXT_GET_TOKEN_V1 = "Get a Sample Authorization Token"
LNK_TXT_GET_TOKEN_V2 = "Get a Sample Authorization Token for v2"
LNK_TXT_AUTH_AS_BENE = "Authorize as a Beneficiary"
LNK_TXT_RESTART_TESTCLIENT = "restart testclient"
# FHIR search result bundle pagination
LNK_TXT_NAV_FIRST = "first"
LNK_TXT_NAV_NEXT = "next"
LNK_TXT_NAV_PREV = "previous"
LNK_TXT_NAV_LAST = "last"
LNK_TXT_NAV_SELF = "self"
# FHIR resources query page
LNK_TXT_PATIENT = "Patient"
LNK_TXT_EOB = "ExplanationOfBenefit"
LNK_TXT_COVERAGE = "Coverage"
LNK_TXT_PROFILE = "Profile"
LNK_TXT_METADATA = "FHIR Metadata"
LNK_TXT_OIDC_DISCOVERY = "OIDC Discovery"
# FHIR result page label H2
LAB_FHIR_RESULTPAGE_H2 = "h2"
CONTENT_FHIR_RESULTPAGE_PRE = "pre"
# MSLSX login form
TXT_FLD_SUB_MSLSX = "username"
TXT_FLD_HICN_MSLSX = "hicn"
TXT_FLD_MBI_MSLSX = "mbi"
TXT_FLD_VAL_SUB_MSLSX = "fred"
MSLSX_TXT_FLD_HICN_VAL = "1000044680"
MSLSX_TXT_FLD_MBI_VAL = "2SW4N00AA00"
MSLSX_CSS_BUTTON = "button"
# SLSX login form
SLSX_TXT_FLD_USERNAME = "username-textbox"
SLSX_TXT_FLD_PASSWORD = "password-textbox"
SLSX_TXT_FLD_USERNAME_VAL = "BBUser00000"
SLSX_TXT_FLD_PASSWORD_VAL = "PW00000!"
SLSX_CSS_BUTTON = "login-button"
# Demographic info access grant form
BTN_ID_GRANT_DEMO_ACCESS = "approve"
BTN_ID_DENY_DEMO_ACCESS = "deny"
BTN_ID_RADIO_NOT_SHARE = "label:nth-child(5)"
# API versions
API_V2 = "v2"
API_V1 = "v1"


class Action(Enum):
    LOAD_PAGE = 1
    FIND_CLICK = 2
    FIND = 3
    FIND_SEND_KEY = 4
    CHECK = 5
    BACK = 6
    LOGIN = 7
    CONTAIN_TEXT = 8
    GET_SAMPLE_TOKEN_START = 9
    SLEEP = 10


BROWSERBACK = {
    "display": "Back to FHIR resource page",
    "action": Action.BACK,
}

WAIT_SECONDS = {
    "display": "Sleep seconds...",
    "action": Action.SLEEP,
    "params": [3],
}

CHECK_TESTCLIENT_START_PAGE = {
    "display": "Check it's on 'Test Client' start page",
    "action": Action.FIND,
    "params": [30, By.LINK_TEXT, LNK_TXT_GET_TOKEN_V1]
}

CLICK_TESTCLIENT = {
    "display": "Click link 'Test Client'",
    "action": Action.FIND_CLICK,
    "params": [30, By.LINK_TEXT, LNK_TXT_TESTCLIENT]
}

CLICK_RADIO_NOT_SHARE = {
    "display": "Click 'Share healthcare data, but not your personal info' on DEMO info grant form",
    "action": Action.FIND_CLICK,
    "params": [20, By.CSS_SELECTOR, BTN_ID_RADIO_NOT_SHARE]
}

CLICK_AGREE_ACCESS = {
    "display": "Click 'Agree' on DEMO info grant form",
    "action": Action.FIND_CLICK,
    "params": [20, By.ID, BTN_ID_GRANT_DEMO_ACCESS]
}

CLICK_DENY_ACCESS = {
    "display": "Click 'Deny' on DEMO info grant form",
    "action": Action.FIND_CLICK,
    "params": [20, By.ID, BTN_ID_DENY_DEMO_ACCESS]
}

CALL_LOGIN = {
    "display": "Start login ...",
    "action": Action.LOGIN,
}

SEQ_LOGIN_MSLSX = [
    {
        "display": "Input SUB(username)",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, TXT_FLD_SUB_MSLSX, TXT_FLD_VAL_SUB_MSLSX]
    },
    {
        "display": "Input hicn",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, TXT_FLD_HICN_MSLSX, MSLSX_TXT_FLD_HICN_VAL]
    },
    {
        "display": "Input mbi",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, TXT_FLD_MBI_MSLSX, MSLSX_TXT_FLD_MBI_VAL]
    },
    {
        "display": "Click 'submit' on MSLSX login form",
        "action": Action.FIND_CLICK,
        "params": [20, By.CSS_SELECTOR, MSLSX_CSS_BUTTON]
    },
]

SEQ_LOGIN_SLSX = [
    {
        "display": "MyMedicare login username",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, SLSX_TXT_FLD_USERNAME, SLSX_TXT_FLD_USERNAME_VAL]
    },
    {
        "display": "MyMedicare login password",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, SLSX_TXT_FLD_PASSWORD, SLSX_TXT_FLD_PASSWORD_VAL]
    },
    {
        "display": "Click 'submit' on SLSX login form",
        "action": Action.FIND_CLICK,
        "params": [20, By.ID, SLSX_CSS_BUTTON]
    },
]

SEQ_AUTHORIZE_START = [
    {
        "display": "Load BB2 Landing Page ...",
        "action": Action.LOAD_PAGE,
        "params": [settings.HOSTNAME_URL]
    },
    CLICK_TESTCLIENT,
    {
        "display": "Click link to get sample token v1/v2",
        "action": Action.GET_SAMPLE_TOKEN_START,
    },
    {
        "display": "Click link 'Authorize as a Beneficiary' - start authorization",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, LNK_TXT_AUTH_AS_BENE]
    },
]

SEQ_QUERY_FHIR_RESOURCES = [
    {
        "display": "Click 'Patient' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_PATIENT]
    },
    {
        "display": "Check Patient result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_PATIENT]
    },
    BROWSERBACK,
    {
        "display": "Click 'Coverage' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_COVERAGE]
    },
    {
        "display": "Check Coverage result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, LNK_TXT_COVERAGE]
    },
    {
        "display": "Check and click Coverage result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_NAV_LAST]
    },
    CLICK_TESTCLIENT,
    {
        "display": "Click 'ExplanationOfBenefit' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_EOB]
    },
    {
        "display": "Check ExplanationOfBenefit result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, LNK_TXT_EOB]
    },
    {
        "display": "Check and click ExplanationOfBenefit result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_NAV_LAST]
    },
    WAIT_SECONDS,
    CLICK_TESTCLIENT,
    WAIT_SECONDS,
    {
        "display": "Click 'Profile' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_PROFILE]
    },
    WAIT_SECONDS,
    {
        "display": "Check Profile result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT,
                   "{} (OIDC Userinfo)".format(LNK_TXT_PROFILE)]
    },
    BROWSERBACK,
    {
        "display": "Click 'FHIR Metadata' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_METADATA]
    },
    {
        "display": "Check FHIR Metadata result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_METADATA]
    },
    BROWSERBACK,
    {
        "display": "Click 'OIDC Discovery' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_OIDC_DISCOVERY]
    },
    {
        "display": "Check OIDC Discovery result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_OIDC_DISCOVERY]
    },
    BROWSERBACK,
]

SEQ_QUERY_FHIR_RESOURCES_NO_DEMO = [
    {
        "display": "Click 'Patient' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_PATIENT]
    },
    {
        "display": "Check Patient result page content (<pre>) expect no permission message",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.TAG_NAME, CONTENT_FHIR_RESULTPAGE_PRE, MESSAGE_NO_PERMISSION]
    },
    BROWSERBACK,
    {
        "display": "Click 'Coverage' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_COVERAGE]
    },
    {
        "display": "Check Coverage result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, LNK_TXT_COVERAGE]
    },
    {
        "display": "Check and click Coverage result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_NAV_LAST]
    },
    CLICK_TESTCLIENT,
    {
        "display": "Click 'ExplanationOfBenefit' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_EOB]
    },
    {
        "display": "Check ExplanationOfBenefit result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, LNK_TXT_EOB]
    },
    {
        "display": "Check and click ExplanationOfBenefit result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_NAV_LAST]
    },
    WAIT_SECONDS,
    CLICK_TESTCLIENT,
    WAIT_SECONDS,
    {
        "display": "Click 'Profile' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_PROFILE]
    },
    WAIT_SECONDS,
    {
        "display": "Check Profile result page content (<pre>) expect no permission message",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.TAG_NAME, CONTENT_FHIR_RESULTPAGE_PRE, MESSAGE_NO_PERMISSION]
    },
    BROWSERBACK,
    {
        "display": "Click 'FHIR Metadata' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_METADATA]
    },
    {
        "display": "Check FHIR Metadata result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_METADATA]
    },
    BROWSERBACK,
    {
        "display": "Click 'OIDC Discovery' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_OIDC_DISCOVERY]
    },
    {
        "display": "Check OIDC Discovery result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_OIDC_DISCOVERY]
    },
    BROWSERBACK,
]

TESTS = {
    "auth_grant_fhir_calls": [
        {"sequence": SEQ_AUTHORIZE_START},
        CALL_LOGIN,
        CLICK_AGREE_ACCESS,
        {"sequence": SEQ_QUERY_FHIR_RESOURCES}
    ],
    "auth_deny_fhir_calls": [
        {"sequence": SEQ_AUTHORIZE_START},
        CALL_LOGIN,
        CLICK_DENY_ACCESS,
        CHECK_TESTCLIENT_START_PAGE
    ],
    "auth_grant_w_no_demo": [
        {"sequence": SEQ_AUTHORIZE_START},
        CALL_LOGIN,
        CLICK_RADIO_NOT_SHARE,
        CLICK_AGREE_ACCESS,
        {"sequence": SEQ_QUERY_FHIR_RESOURCES_NO_DEMO}
    ]
}


class SeleniumTests(TestCase):
    '''
    Test authorization and fhir flow through the built in testclient by
    leveraging selenium web driver (chrome is used)
    '''
    wait_completed = False

    def setUp(self):
        super(SeleniumTests, self).setUp()
        # a bit waiting for selenium service ready for sure
        if not SeleniumTests.wait_completed:
            time.sleep(20)
            SeleniumTests.wait_completed = True
            print("set wait_completed={}".format(SeleniumTests.wait_completed))
        else:
            print("wait_completed={}".format(SeleniumTests.wait_completed))

        opt = webdriver.ChromeOptions()
        opt.add_argument('--headless')
        opt.add_argument("--disable-dev-shm-usage")
        opt.add_argument("--disable-web-security")
        opt.add_argument("--allow-running-insecure-content")
        opt.add_argument("--no-sandbox")
        opt.add_argument("--disable-setuid-sandbox")
        opt.add_argument("--disable-webgl")
        opt.add_argument("--disable-popup-blocking")
        opt.add_argument("--enable-javascript")
        opt.add_argument('--allow-insecure-localhost')
        opt.add_argument('--window-size=1920,1080')
        opt.add_argument("--whitelisted-ips=''")

        self.driver = webdriver.Remote(
            command_executor='http://selenium-hub:4444',
            desired_capabilities=DesiredCapabilities.CHROME, options=opt)

        self.actions = {
            Action.LOAD_PAGE: self._load_page,
            Action.FIND_CLICK: self._find_and_click,
            Action.FIND: self._find_and_return,
            Action.FIND_SEND_KEY: self._find_and_sendkey,
            Action.CHECK: self._check_page_title,
            Action.CONTAIN_TEXT: self._check_page_content,
            Action.GET_SAMPLE_TOKEN_START: self._click_get_sample_token,
            Action.BACK: self._back,
            Action.LOGIN: self._login,
            Action.SLEEP: self._sleep,
        }
        self.use_mslsx = os.environ['USE_MSLSX']
        self.login_seq = SEQ_LOGIN_MSLSX if self.use_mslsx == 'true' else SEQ_LOGIN_SLSX

    def tearDown(self):
        self.driver.quit()
        super(SeleniumTests, self).tearDown()

    def _find_and_click(self, timeout_sec, by, by_expr, **kwargs):
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        self.assertIsNotNone(elem)
        elem.click()
        return elem

    def _testclient_home(self, **kwargs):
        return self._find_and_click(30, By.LINK_TEXT, LNK_TXT_RESTART_TESTCLIENT, **kwargs)

    def _find_and_sendkey(self, timeout_sec, by, by_expr, txt, **kwargs):
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        self.assertIsNotNone(elem)
        elem.send_keys(txt)
        return elem

    def _click_get_sample_token(self, **kwargs):
        return self._find_and_click(30, By.LINK_TEXT,
                                    LNK_TXT_GET_TOKEN_V2 if kwargs.get("api_ver", API_V1) == API_V2 else LNK_TXT_GET_TOKEN_V1)

    def _find_and_return(self, timeout_sec, by, by_expr, **kwargs):
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        self.assertIsNotNone(elem)
        return elem

    def _load_page(self, url, **kwargs):
        self.driver.get(url)

    def _check_page_title(self, timeout_sec, by, by_expr, fmt, resource_type, **kwargs):
        elem = self._find_and_return(timeout_sec, by, by_expr, **kwargs)
        if not (elem.text == fmt.format(resource_type, kwargs.get("api_ver"))):
            print("PAGE:{}".format(self.driver.page_source))
        self.assertEqual(elem.text, fmt.format(resource_type, kwargs.get("api_ver")))

    def _check_page_content(self, timeout_sec, by, by_expr, content_txt, **kwargs):
        elem = self._find_and_return(timeout_sec, by, by_expr, **kwargs)
        self.assertIn(content_txt, elem.text)

    def _back(self, **kwargs):
        self.driver.back()

    def _sleep(self, sec, **kwargs):
        time.sleep(sec)

    def _login(self, step, **kwargs):
        if self.use_mslsx == 'false':
            # dismiss mymedicare popup if present
            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self._play(self.login_seq, step, **kwargs)

    def _print_testcase_banner(self, test_name, api_ver, step_0, id_service, start=True):
        print()
        print("******************************************************************")
        print(TESTCASE_BANNER_FMT.format("START" if start else "END", test_name, api_ver, step_0,
                                         "MSLSX" if id_service == 'true' else "SLSX"))
        print("******************************************************************")
        print()

    def _play(self, lst, step, **kwargs):
        for s in lst:
            seq = s.get("sequence")
            # expects sequence of actions or action
            if seq is not None:
                self._play(seq, step, **kwargs)
            else:
                # single action
                action = s.get('action', None)
                step[0] = step[0] + 1
                if action is not None:
                    print("{}:{}:".format(step[0], s.get("display", "Not available")))
                    if action == Action.LOGIN:
                        self.actions[action](*s.get("params", []), step, **kwargs)
                    else:
                        self.actions[action](*s.get("params", []), **kwargs)
                else:
                    raise ValueError("Invalid test case, expect dict with action...")

    def test_auth_grant_fhir_calls_v1(self):
        step = [0]
        test_name = "auth_grant_fhir_calls"
        api_ver = API_V1
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    def test_auth_grant_fhir_calls_v2(self):
        step = [0]
        test_name = "auth_grant_fhir_calls"
        api_ver = API_V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    def test_auth_deny_fhir_calls_v1(self):
        step = [0]
        test_name = "auth_deny_fhir_calls"
        api_ver = API_V1
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    def test_auth_deny_fhir_calls_v2(self):
        step = [0]
        test_name = "auth_deny_fhir_calls"
        api_ver = API_V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    def test_auth_grant_w_no_demo_v1(self):
        step = [0]
        test_name = "auth_grant_w_no_demo"
        api_ver = API_V1
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)

    def test_auth_grant_w_no_demo_v2(self):
        step = [0]
        test_name = "auth_grant_w_no_demo"
        api_ver = API_V2
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, True)
        self._play(TESTS[test_name], step, api_ver=api_ver)
        self._testclient_home()
        self._print_testcase_banner(test_name, api_ver, step[0], self.use_mslsx, False)
