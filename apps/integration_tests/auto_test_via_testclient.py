import os
import time
from django.conf import settings
from django.test import TestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains


class RunTestClient(TestCase):
    '''
    Test authorization and fhir flow through the built in testclient by
    leveraging selenium web driver (chrome is used)
    '''

    def setUp(self):
        super(RunTestClient, self).setUp()
        opt = webdriver.ChromeOptions()
        opt.add_argument("--headless")
        opt.add_argument("--disable-dev-shm-usage")
        opt.add_argument("--disable-web-security")
        opt.add_argument("--allow-running-insecure-content")
        opt.add_argument("--no-sandbox")
        opt.add_argument("--disable-setuid-sandbox")
        opt.add_argument("--disable-webgl")
        opt.add_argument("--disable-popup-blocking")
        opt.add_argument("--enable-javascript")
        opt.add_argument('--allow-insecure-localhost')
        self.driver = webdriver.Chrome(options=opt)
        # self.driver = webdriver.Remote(command_executor=f"http://localhost:4444",
        #     desired_capabilities=DesiredCapabilities.CHROME,
        #     options=opt,
        # )

    def tearDown(self):
        self.driver.quit()
        super(RunTestClient, self).tearDown()

    def find_and_click(self, timeout_sec, by, by_expr):
        elem = WebDriverWait(self.driver, timeout_sec).until(EC.visibility_of_element_located((by, by_expr)))
        self.assertIsNotNone(elem)
        elem.click()
        return elem

    def test_testclient_01(self):

        self.driver.get("http://localhost:8000/")
        self.driver.set_window_size(1532, 803)
        self.driver.find_element(By.CSS_SELECTOR, ".desktop-nav-items > .signup-button > .feather").click()
        self.driver.find_element(By.ID, "id_first_name").click()
        self.driver.find_element(By.ID, "id_first_name").send_keys("test01")
        self.driver.find_element(By.ID, "id_last_name").send_keys("test01")
        self.driver.find_element(By.ID, "id_email").send_keys("test01@xyz.net")
        self.driver.find_element(By.ID, "id_organization_name").send_keys("XYZ Inc")
        self.driver.find_element(By.ID, "id_password1").click()
        self.driver.find_element(By.ID, "id_password1").send_keys("RedF0x@USA")
        self.driver.find_element(By.ID, "id_password2").send_keys("RedF0x@USA")
        self.driver.find_element(By.CSS_SELECTOR, ".ds-c-button").click()
        print("Next Page.......click sign up")
        print("TITLE={}".format(self.driver.title))
        print(self.driver.page_source.encode("utf-8"))


        # for n, v in os.environ.items():
        #     print("ENV: {} = {}".format(n, v))
        # assume bb2 is on url set by HOSTNAME_URL
        print("HOSTNAME={}".format(settings.HOSTNAME_URL))
        self.driver.get("http://localhost:8000")
        # print(self.driver.page_source.encode("utf-8"))
        print("BB2 Landing Page.....................................")
        # self.driver.get(settings.HOSTNAME_URL)
        # bb2 landing page: click test client link
        
        self.find_and_click(30, By.LINK_TEXT, 'Test Client')
        print("Test Client Page.....................................")
        # self.find_and_click(30, By.ID, 'testclient')
        # test client home page: click link with label text "Get a Sample Authorization Token"
        self.find_and_click(20, By.LINK_TEXT, 'Get a Sample Authorization Token')
        print("Test Client Authorize Page.....................................")
        # test client sample API call page: click link with label text "Authorize as a Beneficiary" id=authorization_url
        self.find_and_click(20, By.LINK_TEXT, 'Authorize as a Beneficiary')
        self.driver.set_window_size(1532, 803)
        # print("------------------------- 30 sec wait -----------------------------")
        # time.sleep(30)
        # support 2 identity providers:
        # 1. MSLS - indicator: HOSTNAME_URL http://192.168.0.109:8000 (e.g. must use local host IP)
        # 2. SLSX - indicator: HOSTNAME_URL http://localhost:8000 - unresolved issue remain
        # if 'localhost' in settings.HOSTNAME_URL:
        #     print("MyMedicare Login Page.....................................")
        #     print(self.driver.page_source.encode("utf-8"))
        #     elem = self.find_and_click(30, By.ID, 'username-textbox')
        #     print("MyMedicare Login user name located .....................................")
        #     # type in synthetic user name
        #     elem.send_keys("BBUser10000")
        #     # focus move to input password
        #     elem = self.find_and_click(20, By.ID, 'password-textbox')
        #     print("MyMedicare Login password located .....................................")
        #     elem.send_keys('PW10000!')
        #     # find the 'Log in' button
        #     self.find_and_click(20, By.ID, 'login-button')
        #     print("MyMedicare Login button located and clicked .....................................")
        # else:
        time.sleep(10)
        print("TITLE={}".format(self.driver.title))

        print(self.driver.page_source.encode("utf-8"))
        elem = self.find_and_click(20, By.NAME, 'username')
        # type in sub name
        elem.send_keys("fred")
        # focus move to input 'hicn' and type in the value
        elem = self.find_and_click(20, By.NAME, 'hicn')
        elem.send_keys('1000044680')
        # focus move to input 'mbi' and type in the value
        elem = self.find_and_click(20, By.NAME, 'mbi')
        elem.send_keys('2SW4N00AA00')
        # find the 'submit' button - note we have only one button on MSLS login page
        self.find_and_click(20, By.CSS_SELECTOR, 'button')

        # scope choose and grant access or deny page - in this path, 'grant' clicked
        self.find_and_click(20, By.ID, 'approve')
        # now on authorized page, access FHIR resources, e.g. Patient
        self.find_and_click(20, By.LINK_TEXT, 'Patient')
        self.assertRegex(self.driver.page_source, r'^.*\"resourceType\":\s*\"Patient\".*$')
        # go back to previous page
        self.driver.back()
        # click EOB
        self.find_and_click(20, By.LINK_TEXT, 'ExplanationOfBenefit')
        self.assertRegex(self.driver.page_source, r'^.*\"resourceType\":\s*\"ExplanationOfBenefit\".*$')
        # go back to previous page
        self.driver.back()
        # click Coverage
        self.find_and_click(20, By.LINK_TEXT, 'Coverage')
        self.assertRegex(self.driver.page_source, r'^.*\"resourceType\":\s*\"Coverage\".*$')

        # go back to previous page
        self.driver.back()
        # click Profile
        self.find_and_click(20, By.LINK_TEXT, 'Profile')
        self.assertRegex(self.driver.page_source, r'^.*\"sub\":\s*\"-20140000008325\".*$')

        # go back to previous page
        self.driver.back()
        # click Meta
        self.find_and_click(20, By.LINK_TEXT, 'FHIR Metadata')
        self.assertRegex(self.driver.page_source, r'^.*\"resourceType\":\s*\"CapabilityStatement\".*$')

        # go back to previous page
        self.driver.back()
        # click OIDC Discovery
        self.find_and_click(20, By.LINK_TEXT, 'OIDC Discovery')
        url_pattern = r'^.*\"service_documentation\":\s*\"https:\/\/bluebutton.cms.gov\/developers\".*$'
        self.assertRegex(self.driver.page_source, url_pattern)
