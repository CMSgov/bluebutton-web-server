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

DISP_BACK = "Back to FHIR resource page"

LNK_TXT_TESTCLIENT = "Test Client"
LNK_TXT_GET_TOKEN_V1 = "Get a Sample Authorization Token"
LNK_TXT_GET_TOKEN_V2 = "Get a Sample Authorization Token for v2"
LNK_TXT_AUTH_AS_BENE = "Authorize as a Beneficiary"
LNK_TXT_RESTART_TESTCLIENT = "restart testclient"

MSLSX_TXT_FLD_SUB = "username"
MSLSX_TXT_FLD_HICN = "hicn"
MSLSX_TXT_FLD_MBI = "mbi"
MSLSX_TXT_FLD_SUB_VAL = "fred"
MSLSX_TXT_FLD_HICN_VAL = "1000044680"
MSLSX_TXT_FLD_MBI_VAL = "2SW4N00AA00"
MSLSX_CSS_BUTTON = "button"

SLSX_TXT_FLD_USERNAME = "username-textbox"
SLSX_TXT_FLD_PASSWORD = "password-textbox"
SLSX_TXT_FLD_USERNAME_VAL = "BBUser00000"
SLSX_TXT_FLD_PASSWORD_VAL = "PW00000!"
SLSX_CSS_BUTTON = "login-button"

GRANT_DEMO_ACCESS = "approve"
DENY_DEMO_ACCESS = "deny"
FHIR_LNK_PATIENT = "Patient"
FHIR_LNK_EOB = "ExplanationOfBenefit"
FHIR_LNK_COVERAGE = "Coverage"
FHIR_LNK_PROFILE = "Profile"
FHIR_LNK_METADATA = "FHIR Metadata"
FHIR_LNK_OIDC_DISCOVERY = "OIDC Discovery"
RESULT_PAGE_TITLE_H2 = "h2"
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


BROWSER_BACK = {
            "display": "Back to FHIR resource page",
            "action": Action.BACK,
            "params": []
        }

FLOW_MSLSX_LOGIN = {
        "mslsx 1": {
            "display": "Input SUB(username)",
            "action": Action.FIND_SEND_KEY,
            "params": [20, By.NAME, MSLSX_TXT_FLD_SUB, MSLSX_TXT_FLD_SUB_VAL]
        },
        "mslsx 2": {
            "display": "Input hicn",
            "action": Action.FIND_SEND_KEY,
            "params": [20, By.NAME, MSLSX_TXT_FLD_HICN, MSLSX_TXT_FLD_HICN_VAL]
        },
        "mslsx 3": {
            "display": "Input mbi",
            "action": Action.FIND_SEND_KEY,
            "params": [20, By.NAME, MSLSX_TXT_FLD_MBI, MSLSX_TXT_FLD_MBI_VAL]
        },
        "mslsx 4": {
            "display": "Click 'submit' on MSLSX login form",
            "action": Action.FIND_CLICK,
            "params": [20, By.CSS_SELECTOR, MSLSX_CSS_BUTTON]
        },
}


FLOW_SLSX_LOGIN = {
        "slsx 1": {
            "display": "MyMedicare login username",
            "action": Action.FIND_SEND_KEY,
            "params": [20, By.ID, SLSX_TXT_FLD_USERNAME, SLSX_TXT_FLD_USERNAME_VAL]
        },
        "slsx 2": {
            "display": "MyMedicare login password",
            "action": Action.FIND_SEND_KEY,
            "params": [20, By.ID, SLSX_TXT_FLD_PASSWORD, SLSX_TXT_FLD_PASSWORD_VAL]
        },
        "slsx 3": {
            "display": "Click 'submit' on SLSX login form",
            "action": Action.FIND_CLICK,
            "params": [20, By.ID, SLSX_CSS_BUTTON]
        },
}


tests = {
    "testcase_v1": {
        "step 1": {
            "display": "Load BB2 Landing Page ...",
            "action": Action.LOAD_PAGE,
            "params": [settings.HOSTNAME_URL]
        },
        "step 2": {
            "display": "Click link 'Test Client'",
            "action": Action.FIND_CLICK,
            "params": [30, By.LINK_TEXT, LNK_TXT_TESTCLIENT]
        },
        "step 3": {
            "display": "Click link to get sample token v2",
            "action": Action.FIND_CLICK,
            "params": [30, By.LINK_TEXT, LNK_TXT_GET_TOKEN_V1]
        },
        "step 4": {
            "display": "Click link 'Authorize as a Beneficiary' - start authorization",
            "action": Action.FIND_CLICK,
            "params": [30, By.LINK_TEXT, LNK_TXT_AUTH_AS_BENE]
        },
        "step 5": {"login": Action.LOGIN},
        "step 6": {
            "display": "Click 'Agree' on DEMO info grant form",
            "action": Action.FIND_CLICK,
            "params": [20, By.ID, GRANT_DEMO_ACCESS]
        },
        "step 7": {
            "display": "Click 'Patient' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_PATIENT]
        },
        "step 8": {
            "display": "Check Patient result page title",
            "api_ver": "v1",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_PATIENT]
        },
        "step 9": BROWSER_BACK,
        "step 10": {
            "display": "Click 'Coverage' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_COVERAGE]
        },
        "step 11": {
            "display": "Check Coverage result page title",
            "api_ver": "v1",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, FHIR_LNK_COVERAGE]
        },
        "step 12": BROWSER_BACK,
        "step 13": {
            "display": "Click 'ExplanationOfBenefit' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_EOB]
        },
        "step 14": {
            "display": "Check ExplanationOfBenefit result page title",
            "api_ver": "v1",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, FHIR_LNK_EOB]
        },
        "step 15": BROWSER_BACK,
        "step 16": {
            "display": "Click 'Profile' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_PROFILE]
        },
        "step 17": {
            "display": "Check Profile result page title",
            "api_ver": "v1",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_RESOURCE_LABEL_FMT,
                       "{} (OIDC Userinfo)".format(FHIR_LNK_PROFILE)]
        },
        "step 18": BROWSER_BACK,
        "step 19": {
            "display": "Click 'FHIR Metadata' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_METADATA]
        },
        "step 20": {
            "display": "Check FHIR Metadata result page title",
            "api_ver": "v1",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_METADATA]
        },
        "step 21": BROWSER_BACK,
        "step 22": {
            "display": "Click 'OIDC Discovery' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_OIDC_DISCOVERY]
        },
        "step 23": {
            "display": "Check OIDC Discovery result page title",
            "api_ver": "v1",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_OIDC_DISCOVERY]
        },
        "step 24": BROWSER_BACK,
    },
    "testcase_v2": {
        "step 1": {
            "display": "Load BB2 Landing Page ...",
            "action": Action.LOAD_PAGE,
            "params": [settings.HOSTNAME_URL]
        },
        "step 2": {
            "display": "Click link 'Test Client'",
            "action": Action.FIND_CLICK,
            "params": [30, By.LINK_TEXT, LNK_TXT_TESTCLIENT]
        },
        "step 3": {
            "display": "Click link to get sample token v2",
            "action": Action.FIND_CLICK,
            "params": [30, By.LINK_TEXT, LNK_TXT_GET_TOKEN_V2]
        },
        "step 4": {
            "display": "Click link 'Authorize as a Beneficiary' - start authorization",
            "action": Action.FIND_CLICK,
            "params": [30, By.LINK_TEXT, LNK_TXT_AUTH_AS_BENE]
        },
        "step 5": {"login": Action.LOGIN},
        "step 6": {
            "display": "Click 'Agree' on DEMO info grant form",
            "action": Action.FIND_CLICK,
            "params": [20, By.ID, GRANT_DEMO_ACCESS]
        },
        "step 7": {
            "display": "Click 'Patient' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_PATIENT]
        },
        "step 8": {
            "display": "Check Patient result page title",
            "api_ver": "v2",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_PATIENT]
        },
        "step 9": BROWSER_BACK,
        "step 10": {
            "display": "Click 'Coverage' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_COVERAGE]
        },
        "step 11": {
            "display": "Check Coverage result page title",
            "api_ver": "v2",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, FHIR_LNK_COVERAGE]
        },
        "step 12": BROWSER_BACK,
        "step 13": {
            "display": "Click 'ExplanationOfBenefit' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_EOB]
        },
        "step 14": {
            "display": "Check ExplanationOfBenefit result page title",
            "api_ver": "v2",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, FHIR_LNK_EOB]
        },
        "step 15": BROWSER_BACK,
        "step 16": {
            "display": "Click 'Profile' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_PROFILE]
        },
        "step 17": {
            "display": "Check Profile result page title",
            "api_ver": "v2",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_RESOURCE_LABEL_FMT,
                       "{} (OIDC Userinfo)".format(FHIR_LNK_PROFILE)]
        },
        "step 18": BROWSER_BACK,
        "step 19": {
            "display": "Click 'FHIR Metadata' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_METADATA]
        },
        "step 20": {
            "display": "Check FHIR Metadata result page title",
            "api_ver": "v2",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_METADATA]
        },
        "step 21": BROWSER_BACK,
        "step 22": {
            "display": "Click 'OIDC Discovery' on FHIR resources page",
            "action": Action.FIND_CLICK,
            "params": [20, By.LINK_TEXT, FHIR_LNK_OIDC_DISCOVERY]
        },
        "step 23": {
            "display": "Check OIDC Discovery result page title",
            "api_ver": "v2",
            "action": Action.CHECK,
            "params": [20, By.TAG_NAME, RESULT_PAGE_TITLE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_OIDC_DISCOVERY]
        },
        "step 24": BROWSER_BACK,
    },
}


class SeleniumTests(TestCase):
    '''
    Test authorization and fhir flow through the built in testclient by
    leveraging selenium web driver (chrome is used)
    '''

    def setUp(self):
        super(SeleniumTests, self).setUp()
        time.sleep(20)
        opt = webdriver.ChromeOptions()
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
            Action.BACK: self._back,
            Action.LOGIN: self._login,
        }
        self.use_mslsx = os.environ['USE_MSLSX']

    def tearDown(self):
        self.driver.quit()
        super(SeleniumTests, self).tearDown()

    def _find_and_click(self, timeout_sec, by, by_expr):
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        self.assertIsNotNone(elem)
        elem.click()
        return elem

    def _testclient_home(self):
        elem = WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.LINK_TEXT, LNK_TXT_RESTART_TESTCLIENT)))
        self.assertIsNotNone(elem)
        elem.click()
        return elem

    def _find_and_sendkey(self, timeout_sec, by, by_expr, txt):
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        self.assertIsNotNone(elem)
        elem.send_keys(txt)
        return elem

    def _find_and_return(self, timeout_sec, by, by_expr):
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        self.assertIsNotNone(elem)
        return elem

    def _load_page(self, url):
        self.driver.get(url)

    def _check_page_title(self, timeout_sec, by, by_expr, fmt, resource_type, api_ver=API_V1):
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, fmt.format(resource_type, api_ver))

    def _back(self):
        self.driver.back()

    def _login(self, flow):
        self._play(flow)

    def _play(self, seq):
        for k, v in seq.items():
            login_func = v.get("login", None)
            if login_func is not None:
                if self.use_mslsx == 'false':
                    # dismiss popup if present
                    webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                    self.actions[login_func](FLOW_SLSX_LOGIN)
                else:
                    self.actions[login_func](FLOW_MSLSX_LOGIN)
            else:
                api_ver = v.get("api_ver")
                print("{}:{}:".format(k, v["display"]))
                if api_ver is not None:
                    self.actions[v["action"]](*v["params"], api_ver=api_ver)
                else:
                    self.actions[v["action"]](*v["params"])

    def test_testclient_v1(self):
        # v1 mslsx/slsx
        self._play(tests["testcase_v1"])
        self._testclient_home()

    def test_testclient_v2(self):
        # v2 mslsx/slsx
        self._play(tests["testcase_v2"])
        self._testclient_home()
