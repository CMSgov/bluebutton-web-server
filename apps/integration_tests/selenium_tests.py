import os
import time
from django.test import TestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

from .selenium_cases import (
    Action,
    TESTCASE_BANNER_FMT,
    LNK_TXT_GET_TOKEN_V1,
    LNK_TXT_GET_TOKEN_V2,
    LNK_TXT_RESTART_TESTCLIENT,
    API_V2,
    API_V1,
    SEQ_LOGIN_MSLSX,
    SEQ_LOGIN_SLSX,
    TESTS,
)


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

        self.use_mslsx = os.environ['USE_MSLSX']
        self.use_grid = os.environ['USE_GRID']
        self.login_seq = SEQ_LOGIN_MSLSX if self.use_mslsx == 'true' else SEQ_LOGIN_SLSX
        print("use_mslsx={}, use_grid={}".format(self.use_mslsx, self.use_grid))

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

        if self.use_grid == 'true':
            self.driver = webdriver.Remote(
                command_executor='http://selenium-hub:4444',
                desired_capabilities=DesiredCapabilities.CHROME, options=opt)
        else:
            opt.add_argument('--headless')
            self.driver = webdriver.Chrome(options=opt)

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
