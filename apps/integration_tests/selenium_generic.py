import os
import time
import re

from apps.integration_tests.common_utils import (
    extract_href_from_html,
    extract_last_part_of_url,
    log_step,
    check_element_state
)
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

from apps.integration_tests.constants import (
    Action,
    TESTCASE_BANNER_FMT,
    TESTCLIENT_LNK_TXT_RESTART,
    SEQ_LOGIN_MSLSX,
    SEQ_LOGIN_SLSX,
    PROD_URL,
    ES_ES,
)

LOG_FILE = './docker-compose/tmp/bb2_email_to_stdout.log'
EN_MONTH_ABBR = ['Jan.', 'Feb.', 'March', 'April', 'May', 'June', 'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.']
ES_MONTH_NAME = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre',
                 'octubre', 'noviembre', 'diciembre']


class SeleniumGenericTests():
    """
    A base selenium tests to be extended by
    other selenium tests covering functional areas

    This is run via pytest, so setup_method and teardown_method are called implicitly

    Raises:
        ValueError: _description_

    """
    driver_ready = False

    def setup_method(self, method):
        # a bit waiting for selenium services ready for sure
        if not SeleniumGenericTests.driver_ready:
            time.sleep(20)
            SeleniumGenericTests.driver_ready = True
            print('set driver_ready={}'.format(SeleniumGenericTests.driver_ready))
        else:
            print('driver_ready={}'.format(SeleniumGenericTests.driver_ready))

        self.environment = os.getenv('TARGET_ENV', '')
        self.on_remote_ci = os.getenv('ON_REMOTE_CI', 'false')
        self.selenium_grid_host = os.getenv('SELENIUM_GRID_HOST', 'chrome')
        self.selenium_grid = os.getenv('SELENIUM_GRID', 'false')
        self.hostname_url = os.environ['HOSTNAME_URL']
        self.use_mslsx = os.environ['USE_MSLSX']
        self.login_seq = SEQ_LOGIN_MSLSX if self.use_mslsx == 'true' else SEQ_LOGIN_SLSX
        msg_fmt = 'use_mslsx={}, hostname_url={}, selenium_grid={}'
        msg = msg_fmt.format(self.use_mslsx, self.hostname_url, self.selenium_grid)
        print(msg)

        opt = webdriver.ChromeOptions()
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--disable-web-security')
        opt.add_argument('--allow-running-insecure-content')
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-setuid-sandbox')
        opt.add_argument('--disable-webgl')
        opt.add_argument('--disable-popup-blocking')
        opt.add_argument('--enable-javascript')
        opt.add_argument('--allow-insecure-localhost')
        opt.add_argument("--whitelisted-ips=''")

        if self.selenium_grid.lower() == 'true':
            # selenium hub
            hub_url = f'http://{self.selenium_grid_host}:4444/wd/hub'
            print('RemoteDriver: grid hub url={hub_url}')
            opt.binary_location = '/usr/bin/chromium'
            self.driver = webdriver.Remote(
                command_executor=hub_url, options=opt)
        else:
            driver_exec = '/usr/local/bin/chromedriver' if self.on_remote_ci.lower() == 'true' else '/usr/bin/chromedriver'
            print(f'Chrome Driver, location={driver_exec}')
            opt.add_argument('--window-size=1920,980')
            opt.add_argument('--headless')
            ser = Service(driver_exec)
            self.driver = webdriver.Chrome(service=ser, options=opt)

        self.actions = {
            Action.LOAD_PAGE: self._load_page,
            Action.FIND_CLICK: self._find_and_click,
            Action.FIND: self._find_and_return,
            Action.FIND_SEND_KEY: self._find_and_sendkey,
            Action.CHECK: self._check_page_title,
            Action.CHECK_PKCE_CHALLENGE: self._check_pkce_challenge,
            Action.CONTAIN_TEXT: self._check_page_content,
            Action.BACK: self._back,
            Action.LOGIN: self._login,
            Action.SLEEP: self._sleep,
            Action.VALIDATE_EMAIL_NOTIFICATION: self._validate_email_content,
            Action.CHECK_DATE_FORMAT: self._check_date_format,
            Action.COPY_LINK_AND_LOAD_WITH_PARAM: self._copy_link_and_load_with_param
        }

    def teardown_method(self, method):
        self.driver.quit()

    def _validate_email_content(self, subj_line, key_line_prefix, **kwargs):
        with open(LOG_FILE, 'r') as f:
            log_records = f.readlines()
            email_subj_cnt = 0
            key_cnt = 0
            ak = None
            while log_records:
                r = log_records.pop(0)
                if r.startswith(subj_line):
                    # print("SUBJ: {}".format(r))
                    email_subj_cnt += 1
                elif key_line_prefix is not None and key_line_prefix in r:
                    # print("KEY: {}".format(r))
                    href = extract_href_from_html(r)
                    ak = extract_last_part_of_url(href)
                    key_cnt += 1
                else:
                    pass
                    # print("NOT COUNTED: {}".format(r))
            # assert one and only one expected email (subj line) found
            # if key_line_prefix is not None - need to extract activation key
            assert email_subj_cnt == 1
            if key_line_prefix is not None:
                assert key_cnt == 1
                assert ak is not None
            return ak

    def _find_and_click(self, timeout_sec, by, by_expr, **kwargs):
        log_step(f"Looking for element to CLICK: {by}='{by_expr}' (timeout: {timeout_sec}s)", 'INFO')

        try:
            elem = WebDriverWait(self.driver, timeout_sec).until(
                EC.element_to_be_clickable((by, by_expr))
            )
            assert elem is not None

            # Log element info before clicking
            text = elem.text[:40] if elem.text else '(no text)'
            log_step(f"Element found, clicking: '{text}'", 'SUCCESS')
            elem.click()
            return elem

        except TimeoutException:
            log_step('TIMEOUT waiting for clickable element', 'ERROR')
            check_element_state(self.driver, by, by_expr, "after timeout")
            raise
        except Exception as e:
            log_step(f'Unexpected error in _find_and_click: {type(e).__name__}', 'ERROR')
            check_element_state(self.driver, by, by_expr, "exception")
            raise

    def _testclient_home(self, **kwargs):
        return self._find_and_click(30, By.LINK_TEXT, TESTCLIENT_LNK_TXT_RESTART, **kwargs)

    def _find_and_sendkey(self, timeout_sec, by, by_expr, txt, **kwargs):
        log_step(f"Looking for element to SEND KEYS: {by}='{by_expr}' (timeout: {timeout_sec}s)", 'INFO')
        print(f"    Keys to send: '{txt}'")

        try:
            elem = WebDriverWait(self.driver, timeout_sec).until(
                EC.visibility_of_element_located((by, by_expr))
            )
            assert elem is not None

            # Log element details
            elem_tag = elem.tag_name
            elem_type = elem.get_attribute('type') or 'text'
            elem_name = elem.get_attribute('name') or elem.get_attribute('id') or '(no name)'
            log_step(f"Element found: <{elem_tag}> type='{elem_type}' name='{elem_name}'", 'SUCCESS')
            elem.send_keys(txt)
            log_step('Keys sent successfully', 'SUCCESS')
            return elem

        except TimeoutException:
            log_step('TIMEOUT waiting for visible element', 'ERROR')
            print(f"\tWaited {timeout_sec} seconds for: {by}='{by_expr}'")

            check_element_state(self.driver, by, by_expr, "after timeout")
            raise
        except Exception as e:
            log_step(f'Unexpected error in _find_and_sendkey: {type(e).__name__}', 'ERROR')
            check_element_state(self.driver, by, by_expr, "exception")
            raise

    def _find_and_return(self, timeout_sec, by, by_expr, **kwargs):
        log_step(f"Looking for element: {by}='{by_expr}' (timeout: {timeout_sec}s)", 'INFO')

        try:
            elem = WebDriverWait(self.driver, timeout_sec).until(
                EC.visibility_of_element_located((by, by_expr))
            )
            assert elem is not None
            log_step("Element found", 'SUCCESS')
            return elem
        except TimeoutException:
            log_step('TIMEOUT waiting for element', 'ERROR')
            check_element_state(self.driver, by, by_expr, "after timeout")
            raise
        except Exception as e:
            log_step(f'Unexpected error: {type(e).__name__}', 'ERROR')
            check_element_state(self.driver, by, by_expr, "exception")
            raise

    def _load_page(self, url, **kwargs):
        if url == PROD_URL or url == PROD_URL + '/':
            print('Skip loading page: {}'.format(url))
        else:
            log_step(f"Loading page: {url}", 'INFO')
            self.driver.get(url)
            log_step(f'Page loaded: {self.driver.title}', 'SUCCESS')

    def _check_page_title(self, timeout_sec, by, by_expr, fmt, resource_type, **kwargs):
        elem = self._find_and_return(timeout_sec, by, by_expr, **kwargs)
        expected = fmt.format(resource_type, kwargs.get("api_ver"))
        if not (elem.text == expected):
            log_step('Page title mismatch!', 'ERROR')
            print(f"\tExpected: '{expected}'")
            print(f"\tGot: '{elem.text}'")
        assert elem.text == expected

    def _check_pkce_challenge(self, timeout_sec, by, by_expr, pkce, **kwargs):
        elem = self._find_and_return(timeout_sec, by, by_expr, **kwargs)
        if pkce:
            assert (('code_challenge' in elem.text and 'code_challenge_method' in elem.text))
        else:
            assert not (('code_challenge' in elem.text or 'code_challenge_method' in elem.text))

    def _check_page_content(self, timeout_sec, by, by_expr, content_txt, **kwargs):
        elem = self._find_and_return(timeout_sec, by, by_expr, **kwargs)
        assert content_txt in elem.text

    def _check_date_format(self, timeout_sec, by, by_expr, format, lang, **kwargs):
        elem = self._find_and_return(timeout_sec, by, by_expr, **kwargs)
        pattern = re.compile(format)
        m = pattern.match(elem.text)
        print(f'date: {elem.text}')
        assert m is not None, f"Date value '{elem.text}' doesn't match expected format"
        try:
            day = m.group('day')
            month = m.group('month')
            year = m.group('year')
            month_num = -1
            try:
                if lang == ES_ES:
                    # for ES_ES, month is full name
                    # locale.setlocale(locale.LC_ALL, ES_ES) - choose not to use locale package (it might be thread unsafe)
                    # use a pre-built array to do month name -> month num mapping
                    month_num = ES_MONTH_NAME.index(month)
                else:
                    # for EN_US, month is abbr
                    month_num = EN_MONTH_ABBR.index(month)
            except ValueError as v:
                print(v)
                assert 1 < 0, f"Month value '{month}' is not recognized."
            if month_num >= 0:
                expire_date = datetime(int(year), month_num + 1, int(day))
                expected_exp_date = datetime.today() + relativedelta(months=+13)
                # Allow 1 day of wiggle room to ignore hour/min/sec
                dates_match = timedelta(days=-1) < expire_date - expected_exp_date < timedelta(days=1)
                assert dates_match, f"Expiration date is '{expire_date}', expected '{expected_exp_date}."
            else:
                assert 1 < 0, f"Month value '{month}' is not recognized."
        except IndexError as e:
            # bad date value
            print(e)
            assert 1 < 0, f"Malformed date value '{elem.text}'"

    def _copy_link_and_load_with_param(self, timeout_sec, by, by_expr, **kwargs):
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        assert elem is not None
        url = f"{elem.get_attribute('href')}&lang=es"
        log_step(f'Copying link and adding param: {url}', 'INFO')
        self.driver.get(url)

    def _back(self, **kwargs):
        log_step('Navigating back', 'INFO')
        self.driver.back()

    def _sleep(self, sec, **kwargs):
        log_step(f'Sleeping for {sec} seconds', 'INFO')
        time.sleep(sec)

    def _login(self, step, **kwargs):
        log_step('Starting login sequence', 'INFO')
        if self.use_mslsx == 'false':
            # dismiss Medicare.gov popup if present
            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self._play(self.login_seq, step, **kwargs)
        log_step('Login sequence completed', 'SUCCESS')

    def _print_testcase_banner(self, test_name, api_ver, step_0, id_service, start=True):
        print('\n******************************************************************')
        print(TESTCASE_BANNER_FMT.format('START' if start else 'END', test_name, api_ver, step_0,
                                         'Mock SLS' if id_service == 'true' else 'SLSX'))
        print(f"** Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('******************************************************************\n')

    def _play(self, lst, step, **kwargs):
        for s in lst:
            seq = s.get('sequence')
            # expects sequence of actions or action
            if seq is not None:
                self._play(seq, step, **kwargs)
            else:
                # single action
                action = s.get('action', None)
                step[0] = step[0] + 1

                if action is not None:
                    display_msg = s.get('display', 'Not available')
                    print(f"\n{'─' * 80}")
                    print(f'{step[0]}:{display_msg}')
                    try:
                        if action == Action.LOGIN:
                            self.actions[action](*s.get('params', []), step, **kwargs)
                        else:
                            self.actions[action](*s.get('params', []), **kwargs)
                    except TimeoutException as timeout:
                        print(f'{timeout.msg}')
                        log_step(f'Step {step[0]} FAILED with TimeoutException', 'ERROR')
                        print(f'\tAction: {action}')
                        print(f'\tDisplay: {display_msg}')
                        raise
                    except Exception as e:
                        log_step(f'Step {step[0]} FAILED with {type(e).__name__}', 'ERROR')
                        print(f'\tAction: {action}')
                        print(f'\tDisplay: {display_msg}')
                        print(f'\tError: {str(e)[:200]}')
                        raise
                else:
                    raise ValueError('Invalid test case, expect dict with action...')
