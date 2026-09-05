import os
import re
import time
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from apps.integration_tests.common_utils import (
    check_element_state,
    extract_href_from_html,
    extract_last_part_of_url,
    log_step,
)
from apps.integration_tests.constants import (
    ES_ES,
    MSLSX_BTN_SUBMIT,
    MSLSX_TXT_FLD_HICN,
    MSLSX_TXT_FLD_MBI,
    MSLSX_TXT_FLD_USERNAME,
    PROD_URL,
    SLSX_CSS_CONTINUE_BUTTON,
    SLSX_CSS_LOGIN_BUTTON,
    SLSX_TXT_FLD_PASSWORD,
    SLSX_TXT_FLD_USERNAME,
    TESTCASE_BANNER_FMT,
    TESTCLIENT_LNK_TXT_RESTART,
    WAIT_SECONDS,
    X_PATH_FOR_MEDICARE_LOGIN,
    Action,
)

LOG_FILE = './docker-compose/tmp/bb2_email_to_stdout.log'
EN_MONTH_ABBR = ['Jan.', 'Feb.', 'March', 'April', 'May', 'June', 'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.']
ES_MONTH_NAME = [
    'enero',
    'febrero',
    'marzo',
    'abril',
    'mayo',
    'junio',
    'julio',
    'agosto',
    'septiembre',
    'octubre',
    'noviembre',
    'diciembre',
]


class SeleniumGenericTests:
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
            self.driver = webdriver.Remote(command_executor=hub_url, options=opt)
        else:
            driver_exec = (
                '/usr/local/bin/chromedriver' if self.on_remote_ci.lower() == 'true' else '/usr/bin/chromedriver'
            )
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
            Action.COPY_LINK_AND_LOAD_WITH_PARAM: self._copy_link_and_load_with_param,
        }

    def teardown_method(self, method):
        self.driver.quit()

    def _validate_email_content(self, subj_line: str, key_line_prefix: str, **kwargs) -> str:
        """
        Validate that an email with the specified subject line and key line prefix has been sent.

        Args:
            subj_line (str): The subject line to look for in the email log.
            key_line_prefix (str): The prefix of the key line to look for in the email log.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            str: The extracted activation key, if found.
        """
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

    def _find_and_click(self, timeout_sec: int, by: By, by_expr: str, **kwargs) -> WebElement:
        """
        Find an element on the page and click it.

        Args:
            timeout_sec (int): The maximum time to wait for the element to be visible.
            by (By): The method to locate the element (e.g., By.ID, By.NAME, By.XPATH).
            by_expr (str): The expression to locate the element (e.g., the ID, name, or XPath).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            WebElement: The found element.
        Raises:
            TimeoutException: If the element is not found within the specified timeout.
            Exception: For any other unexpected errors during the element search.
        """
        log_step(f"Looking for element to CLICK: {by}='{by_expr}' (timeout: {timeout_sec}s)", 'INFO')

        try:
            elem = WebDriverWait(self.driver, timeout_sec).until(EC.element_to_be_clickable((by, by_expr)))
            assert elem is not None

            # Log element info before clicking
            text = elem.text[:40] if elem.text else '(no text)'
            log_step(f"Element found, clicking: '{text}'", 'SUCCESS')
            elem.click()
            return elem

        except TimeoutException:
            # This is related to BB2-4503. The new CSPs are available in some environments, but not all. To work around
            # this we will allow a TimeoutException to be raised without failing the test if the element we are trying to
            # click is the Medicare login button
            if by_expr == X_PATH_FOR_MEDICARE_LOGIN:
                log_step('Element not found but expected for Medicare login, skipping click', 'WARNING')
                return

            log_step('TIMEOUT waiting for clickable element', 'ERROR')
            check_element_state(self.driver, by, by_expr, 'after timeout')
            raise
        except Exception as e:
            log_step(f'Unexpected error in _find_and_click: {type(e).__name__}', 'ERROR')
            check_element_state(self.driver, by, by_expr, 'exception')
            raise

    def _testclient_home(self, **kwargs) -> WebElement:
        """
        Click on the "Restart" link on the test client home page to reset the state for the next test.

        Args:
            **kwargs: Arbitrary keyword arguments. These are not used in this function
                but are included for consistency with other action methods.

        Returns:
            WebElement: The found "Restart" link element.
        """
        return self._find_and_click(30, By.LINK_TEXT, TESTCLIENT_LNK_TXT_RESTART, **kwargs)

    def _find_and_sendkey(self, timeout_sec: int, by: By, by_expr: str, txt: str, **kwargs) -> WebElement:
        """
        Find an element on the page and send keys to it.

        Args:
            timeout_sec (int): The maximum time to wait for the element to be visible.
            by (By): The method to locate the element (e.g., By.ID, By.NAME, By.XPATH).
            by_expr (str): The expression to locate the element (e.g., the ID, name, or XPath).
            txt (str): The text to send to the element.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            WebElement: The found element.
        Raises:
            TimeoutException: If the element is not found within the specified timeout.
            Exception: For any other unexpected errors during the element search.
        """
        log_step(f"Looking for element to SEND KEYS: {by}='{by_expr}' (timeout: {timeout_sec}s)", 'INFO')
        print(f"    Keys to send: '{txt}'")

        try:
            elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
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

            check_element_state(self.driver, by, by_expr, 'after timeout')
            raise
        except Exception as e:
            log_step(f'Unexpected error in _find_and_sendkey: {type(e).__name__}', 'ERROR')
            check_element_state(self.driver, by, by_expr, 'exception')
            raise

    def _find_and_return(self, timeout_sec: int, by: By, by_expr: str, **kwargs) -> WebElement:
        """
        Find an element on the page and return it.

        Args:
            timeout_sec (int): The maximum time to wait for the element to be visible.
            by (By): The method to locate the element (e.g., By.ID, By.NAME, By.XPATH).
            by_expr (str): The expression to locate the element (e.g., the ID, name, or XPath).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            WebElement: The found element.
        Raises:
            TimeoutException: If the element is not found within the specified timeout.
            Exception: For any other unexpected errors during the element search.
        """
        log_step(f"Looking for element: {by}='{by_expr}' (timeout: {timeout_sec}s)", 'INFO')

        try:
            elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
            assert elem is not None
            log_step('Element found', 'SUCCESS')
            return elem
        except TimeoutException:
            log_step('TIMEOUT waiting for element', 'ERROR')
            check_element_state(self.driver, by, by_expr, 'after timeout')
            raise
        except Exception as e:
            log_step(f'Unexpected error: {type(e).__name__}', 'ERROR')
            check_element_state(self.driver, by, by_expr, 'exception')
            raise

    def _load_page(self, url: str, **kwargs) -> None:
        """
        Load a web page using the Selenium web driver.

        Args:
            url (str): The URL of the page to load.
            **kwargs: Arbitrary keyword arguments.
        Returns:
            None. The function loads the page and logs the action.
        """
        if url == PROD_URL or url == PROD_URL + '/':
            print('Skip loading page: {}'.format(url))
        else:
            log_step(f'Loading page: {url}', 'INFO')
            self.driver.get(url)
            log_step(f'Page loaded: {self.driver.title}', 'SUCCESS')

    def _check_page_title(self, timeout_sec: int, by: By, by_expr: str, fmt: str, resource_type: str, **kwargs) -> None:
        """
        Check that the page title matches the expected format.

        Args:
            timeout_sec (int): The maximum time to wait for the element to be visible.
            by (By): The method to locate the element (e.g., By.ID, By.NAME, By.XPATH).
            by_expr (str): The expression to locate the element (e.g., the ID, name, or XPath).
            fmt (str): The format string for the expected page title.
            resource_type (str): The type of the resource.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None. The function performs the validation and raises an AssertionError if the page title
            does not match the expected format.
        """
        elem = self._find_and_return(timeout_sec, by, by_expr, **kwargs)
        expected = fmt.format(resource_type, kwargs.get('api_ver'))
        if not (elem.text == expected):
            log_step('Page title mismatch!', 'ERROR')
            print(f"\tExpected: '{expected}'")
            print(f"\tGot: '{elem.text}'")
        assert elem.text == expected

    def _check_pkce_challenge(self, timeout_sec: int, by: By, by_expr: str, pkce: bool, **kwargs) -> None:
        """
        Check if the PKCE challenge is present or absent in the page content.

        Args:
            timeout_sec (int): The maximum time to wait for the element to be visible.
            by (By): The method to locate the element (e.g., By.ID, By.NAME, By.XPATH).
            by_expr (str): The expression to locate the element (e.g., the ID, name, or XPath).
            pkce (bool): Whether the PKCE challenge should be present.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None. The function performs the validation and raises an AssertionError if the PKCE challenge
            is not found when it should be or if the PKCE challenge is found when it should not be.
        """
        elem = self._find_and_return(timeout_sec, by, by_expr, **kwargs)
        if pkce:
            assert 'code_challenge' in elem.text and 'code_challenge_method' in elem.text
        else:
            assert not ('code_challenge' in elem.text or 'code_challenge_method' in elem.text)

    def _check_page_content(
        self, timeout_sec: int, by: By, by_expr: str, content_txt: str, should_exist: bool = True, **kwargs
    ) -> None:
        """
        Check if the specified content text is present or absent in the page content.

        Args:
            timeout_sec (int): The maximum time to wait for the element to be visible.
            by (By): The method to locate the element (e.g., By.ID, By.NAME, By.XPATH).
            by_expr (str): The expression to locate the element (e.g., the ID, name, or XPath).
            content_txt (str): The text to search for in the page content.
            should_exist (bool): Whether the text should exist in the page content.
            **kwargs: Arbitrary keyword arguments. These are not used in this function
                but are included for consistency with other action methods.

        Returns:
            None. The function performs the validation and raises an AssertionError if the text
            is not found when it should be or if the text is found when it should not be.
        """
        elem = self._find_and_return(timeout_sec, by, by_expr, **kwargs)
        if should_exist:
            assert content_txt in elem.text
        else:
            assert content_txt not in elem.text

    def _check_date_format(self, timeout_sec: int, by: By, by_expr: str, format: str, lang: str, **kwargs) -> None:
        """
        Check that the date format of the element matches the expected format.

        Args:
            timeout_sec (int): The maximum time to wait for the element to be visible.
            by (By): The method to locate the element (e.g., By.ID, By.NAME, By.XPATH).
            by_expr (str): The expression to locate the element (e.g., the ID, name, or XPath).
            format (str): The expected date format as a regular expression.
            lang (str): The language code (e.g., 'en' for English, 'es' for Spanish) to determine the month format.
            **kwargs: Arbitrary keyword arguments. These are not used in this function
                but are included for consistency with other action methods.

        Returns:
            None. The function performs the validation and raises an AssertionError if the date format
            does not match the expected format or if the date is not within the expected range.
        """
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

    def _copy_link_and_load_with_param(self, timeout_sec: int, by: By, by_expr: str, **kwargs) -> None:
        """
        Copy the href from an element and load it with an additional parameter.

        Args:
            timeout_sec (int): The maximum time to wait for the element to be visible.
            by (By): The method to locate the element (e.g., By.ID, By.NAME, By.XPATH).
            by_expr (str): The expression to locate the element (e.g., the ID, name, or XPath).
            **kwargs: Arbitrary keyword arguments. These are not used in this function but
                are included for consistency with other action methods.
        Returns:
            None. The function performs the action and does not return any value.
        """
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        assert elem is not None
        url = f'{elem.get_attribute("href")}&lang=es'
        log_step(f'Copying link and adding param: {url}', 'INFO')
        self.driver.get(url)

    def _back(self, **kwargs) -> None:
        """
        Navigate back to the previous page in the browser history.

        Args:
            **kwargs: Arbitrary keyword arguments. These are not used in this function
                but are included for consistency with other action methods.

        Returns:
            None. The function performs the navigation and does not return any value.
        """
        log_step('Navigating back', 'INFO')
        self.driver.back()

    def _sleep(self, sec: int, **kwargs) -> None:
        """
        Sleep for a specified number of seconds.

        Args:
            sec (int): The number of seconds to sleep.
            **kwargs: Arbitrary keyword arguments. These are not used in this function
                but are included for consistency with other action methods.

        Returns:
            None. The function performs the sleep operation and does not return any value.
        """
        log_step(f'Sleeping for {sec} seconds', 'INFO')
        time.sleep(sec)

    def _login(self, *params, step, **kwargs):
        """
        Login sequence for a synthetic beneficiary, used in both MSLSX and SLSX login.

        Args:
            *params: Variable length argument list. The parameters are expected to be in the order of
                username, hicn, mbi for MSLSX and username, password for SLSX.
            step: A list containing the current step number. This is used to keep
                track of the step number across recursive calls.
            **kwargs: Arbitrary keyword arguments. These are passed to the underlying _play method.

        Returns:
            None. The function performs the login sequence and does not return any value.
        """
        log_step('Starting login sequence', 'INFO')
        if self.use_mslsx == 'true':
            self._play(self._get_login_mslsx_sequence(*params), step, **kwargs)
        else:
            self._play(self._get_login_slsx_sequence(*params), step, **kwargs)
        log_step('Login sequence completed', 'SUCCESS')

    def _print_testcase_banner(self, test_name, api_ver, step_0, id_service, start=True):
        """
        Print a banner indicating the start or end of a test case.

        Args:
            test_name (str): The name of the test case.
            api_ver (str): The API version being tested.
            step_0 (int): The current step number.
            id_service (str): The identity service being used ('true' for Mock SLS, 'false' for SLSX).
            start (bool): True if the banner is for the start of the test case, False if it is for the end.

        Returns:
            None. The function prints the banner and does not return any value.
        """
        print('\n******************************************************************')
        print(
            TESTCASE_BANNER_FMT.format(
                'START' if start else 'END', test_name, api_ver, step_0, 'Mock SLS' if id_service == 'true' else 'SLSX'
            )
        )
        print(f'** Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('******************************************************************\n')

    def _play(self, lst: list, step: list, **kwargs) -> None:
        """
        Play a sequence of actions defined in a list of dictionaries.
        Each dictionary should contain an 'action' key.

        Args:
            lst (list): A list of dictionaries, each representing an action to perform.
            step (list): A list containing the current step number. This is used to keep track of the step number across recursive calls.
            **kwargs: Arbitrary keyword arguments. These are passed to the underlying action methods.
        Returns:
            None. The function performs the actions and does not return any value.
        """
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
                    print(f'\n{"─" * 80}')
                    print(f'{step[0]}:{display_msg}')
                    try:
                        if action == Action.LOGIN:
                            self.actions[action](*s.get('params', []), step=step, **kwargs)
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

    def _get_login_mslsx_sequence(self, username: str, hicn: str, mbi: str, **kwargs) -> list[dict[str, any]]:
        """
        Generates a dynamic login sequence with configurable credentials.

        Args:
            username (str): The username to use for login.
            hicn (str): The HICN to use for login.
            mbi (str): The MBI to use for login.
            **kwargs: Arbitrary keyword arguments.
        Returns:
            list: A list of dictionaries representing the login sequence.
        """
        return [
            {
                'display': 'Input SUB(username)',
                'action': Action.FIND_SEND_KEY,
                'params': [20, By.NAME, MSLSX_TXT_FLD_USERNAME, username],
            },
            {
                'display': 'Input hicn',
                'action': Action.FIND_SEND_KEY,
                'params': [20, By.NAME, MSLSX_TXT_FLD_HICN, hicn],
            },
            {
                'display': 'Input mbi',
                'action': Action.FIND_SEND_KEY,
                'params': [20, By.NAME, MSLSX_TXT_FLD_MBI, mbi],
            },
            {
                'display': "Click 'submit' on MSLSX login form",
                'action': Action.FIND_CLICK,
                'params': [20, By.CSS_SELECTOR, MSLSX_BTN_SUBMIT],
            },
        ]

    def _get_login_slsx_sequence(self, username: str, password: str, **kwargs) -> list[dict[str, any]]:
        """
        Generates a dynamic login sequence with configurable credentials for SLSX.

        Args:
            username (str): The username to use for login.
            password (str): The password to use for login.
            **kwargs: Arbitrary keyword arguments.
        Returns:
            list: A list of dictionaries representing the login sequence.
        """
        return [
            {
                'display': 'Click on Medicare.gov option - continue authorization',
                'action': Action.FIND_CLICK,
                'params': [15, By.XPATH, X_PATH_FOR_MEDICARE_LOGIN],
            },
            {
                'display': 'Medicare.gov login username',
                'action': Action.FIND_SEND_KEY,
                'params': [20, By.NAME, SLSX_TXT_FLD_USERNAME, username],
            },
            {
                'display': "Click 'Continue' on SLSX login form",
                'action': Action.FIND_CLICK,
                'params': [20, By.CSS_SELECTOR, SLSX_CSS_CONTINUE_BUTTON],
            },
            WAIT_SECONDS,
            {
                'display': 'Medicare.gov login password',
                'action': Action.FIND_SEND_KEY,
                'params': [20, By.NAME, SLSX_TXT_FLD_PASSWORD, password],
            },
            {
                'display': "Click 'Log In' on SLSX login form",
                'action': Action.FIND_CLICK,
                'params': [20, By.XPATH, SLSX_CSS_LOGIN_BUTTON],
            },
            WAIT_SECONDS,
        ]
