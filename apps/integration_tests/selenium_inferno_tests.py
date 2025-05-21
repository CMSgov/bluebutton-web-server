import time
import os

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from .selenium_generic import SeleniumGenericTests
from .selenium_cases import (
    SLSX_TXT_FLD_PASSWORD_VAL,
    SLSX_TXT_FLD_USERNAME_VAL
)

USE_NEW_PERM_SCREEN = "true"


class TestInfernoSuites(SeleniumGenericTests):
    def test_inferno_suites(self):
        self.inferno_url = os.getenv('INFERNO_URL', 'http://localhost')
        self.test_app_client_id = os.getenv('CLIENT_ID_4_INFERNO_TEST', 'client_id_of_built_in_testapp')
        # recently created SSM entry return the result in the form of {secret_id:secretvalue}
        # extract the value if so
        self.test_app_client_id = self._extract_value(self.test_app_client_id)
        self.test_app_client_secret = os.getenv('CLIENT_SECRET_4_INFERNO_TEST', 'client_secret_of_built_in_testapp')
        self.test_app_client_secret = self._extract_value(self.test_app_client_secret)

        driver = self.driver
        driver.get(self.inferno_url)
        # in this recorded raw code, sleep called before each find element call to allow dom model to populate and the widget
        # become visible, if we use BB2 selenium ACTION FIND_CLICK (call WebDriverWait under hood)
        # e.g. it will be with 30 sec timeout
        # TODO: convert into BB2 selenium test ACTIONs...
        time.sleep(2)
        driver.find_element(By.XPATH, "//*[text()='SMART App Launch STU2.2']").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "//div[@id='root']/div/div[2]/div/div/div[2]/div/div[3]/div/span").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[@type='button']").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "//div[@id='root']/div/div/main/div/div/div/span[2]/button").click()
        time.sleep(2)
        driver.find_element(By.ID, "input0_text").click()
        time.sleep(2)
        driver.find_element(By.ID, "input0_text").clear()
        time.sleep(2)
        driver.find_element(By.ID, "input0_text").send_keys("{}/v2/fhir/".format(self.hostname_url))
        time.sleep(2)
        driver.find_element(By.ID, "input1_autocomplete").click()
        time.sleep(2)
        driver.find_element(By.ID, "input1_autocomplete-option-1").click()
        time.sleep(2)
        # clear preset scope and put in bb2 scope
        driver.find_element(By.ID, "input3_text").click()
        time.sleep(5)
        driver.find_element(By.ID, "input3_text").clear()
        time.sleep(5)
        scope = "launch/patient openid patient/Patient.rs patient/Coverage.rs patient/ExplanationOfBenefit.rs"
        driver.find_element(By.ID, "input3_text").send_keys(scope)
        time.sleep(5)
        # click client id field and put in value
        driver.find_element(By.ID, "input4_text").click()
        time.sleep(5)
        driver.find_element(By.ID, "input4_text").send_keys(self.test_app_client_id)
        time.sleep(5)
        # click client secret field and put in value
        driver.find_element(By.ID, "input5_text").click()
        time.sleep(5)
        driver.find_element(By.ID, "input5_text").send_keys(self.test_app_client_secret)
        time.sleep(5)
        # click client id field and put in value AGAIN
        driver.find_element(By.ID, "input4_text").click()
        time.sleep(5)
        # challenge: SUBMIT button refuse to become active in selenium play which prevent
        # test proceed
        elem = WebDriverWait(
            self.driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".MuiButton-containedSizeMedium")))
        if elem:
            # attempt force click by exec javascript (not working yet)
            driver.execute_script("arguments[0].click();", elem)
        else:
            print("Submit not visible in 30 sec...")
        # if submit got clicked, there is period before a user action dialog popup
        time.sleep(50)
        # below is the inferno user action dialog
        driver.find_element(By.LINK_TEXT, "Follow this link to authorize with the SMART server").click()
        time.sleep(5)
        driver.find_element(By.ID, "username-textbox").click()
        time.sleep(5)
        driver.find_element(By.ID, "username-textbox").clear()
        time.sleep(5)
        driver.find_element(By.ID, "username-textbox").send_keys(SLSX_TXT_FLD_USERNAME_VAL)
        time.sleep(5)
        driver.find_element(By.ID, "password-textbox").click()
        time.sleep(5)
        driver.find_element(By.ID, "password-textbox").clear()
        time.sleep(5)
        driver.find_element(By.ID, "password-textbox").send_keys(SLSX_TXT_FLD_PASSWORD_VAL)
        time.sleep(5)
        driver.find_element(By.ID, "login-button").click()
        time.sleep(5)
        time.sleep(5)
        driver.find_element(By.ID, "approve").click()
        time.sleep(5)

    def _extract_value(self, s):
        if s is not None and s.startswith("{"):
            ll = s.strip("{}").split(":")
            return ll[1]
        return s
