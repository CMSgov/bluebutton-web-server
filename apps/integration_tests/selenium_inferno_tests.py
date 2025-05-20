import time
import os

from .selenium_generic import SeleniumGenericTests

from selenium.webdriver.common.by import By

USE_NEW_PERM_SCREEN = "true"


class TestInfernoSuites(SeleniumGenericTests):
    def test_inferno_suites(self):
        self.test_app_client_id = os.getenv('CLIENT_ID_4_INFERNO_TEST', 'client_id_of_built_in_testapp')
        self.test_app_client_secret = os.getenv('CLIENT_SECRET_4_INFERNO_TEST', 'client_secret_of_built_in_testapp')

        driver = self.driver
        driver.get("http://192.168.0.146/")
        time.sleep(5)
        driver.find_element(By.XPATH, "//*[text()='SMART App Launch STU2.2']").click()
        time.sleep(5)
        driver.find_element(By.XPATH, "//div[@id='root']/div/div[2]/div/div/div[2]/div/div[3]/div/span").click()
        time.sleep(5)
        driver.find_element(By.XPATH, "//button[@type='button']").click()
        time.sleep(5)
        driver.find_element(By.XPATH, "//div[@id='root']/div/div/main/div/div/div/span[2]/button").click()
        time.sleep(5)
        driver.find_element(By.ID, "input0_text").click()
        time.sleep(5)
        driver.find_element(By.ID, "input0_text").clear()
        time.sleep(5)
        driver.find_element(By.ID, "input0_text").send_keys("http://192.168.0.146:8000/v2/fhir/")
        time.sleep(5)
        driver.find_element(By.ID, "input1_autocomplete").click()
        time.sleep(5)
        driver.find_element(By.ID, "input1_autocomplete-option-1").click()
        time.sleep(5)
        # clear preset scope and put in bb2 scope
        driver.find_element(By.ID, "input3_text").click()
        time.sleep(5)
        driver.find_element(By.ID, "input3_text").clear()
        time.sleep(5)
        driver.find_element(By.ID, "input3_text").send_keys("launch/patient openid patient/Patient.rs patient/Coverage.rs patient/ExplanationOfBenefit.rs")
        time.sleep(5)
        # click client id field and put in value
        driver.find_element(By.ID, "input4_text").click()
        time.sleep(5)
        driver.find_element(By.ID, "input4_text").send_keys("client_id_of_built_in_testapp")
        time.sleep(5)
        # click client secret field and put in value
        driver.find_element(By.ID, "input5_text").click()
        time.sleep(5)
        driver.find_element(By.ID, "input5_text").send_keys("client_secret_of_built_in_testapp")
        time.sleep(5)
        driver.find_element(By.XPATH, "(.//*[normalize-space(text()) and normalize-space(.)='Submit'])[1]/following::button[2]").click()
        time.sleep(5)
        driver.find_element(By.LINK_TEXT, "Follow this link to authorize with the SMART server").click()
        time.sleep(5)
        driver.get("https://test.medicare.gov/account/login/?client_id=bb2api&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fmymedicare%2Fsls-callback&relay=64664239213351163188174627")
        time.sleep(5)
        driver.find_element(By.ID, "username-textbox").click()
        time.sleep(5)
        driver.find_element(By.ID, "username-textbox").clear()
        time.sleep(5)
        driver.find_element(By.ID, "username-textbox").send_keys("BBUser00000")
        time.sleep(5)
        driver.find_element(By.ID, "password-textbox").click()
        time.sleep(5)
        driver.find_element(By.ID, "password-textbox").clear()
        time.sleep(5)
        driver.find_element(By.ID, "password-textbox").send_keys("PW00000!")
        time.sleep(5)
        driver.find_element(By.ID, "login-button").click()
        time.sleep(5)
        driver.get("http://localhost:8000/v2/o/authorize/61f693ec-cb8b-4959-b32c-48ff839b45a4/?response_type=code&client_id=client_id_of_built_in_testapp&redirect_uri=http%3A%2F%2Flocalhost%2Fcustom%2Fsmart_stu2_2%2Fredirect&scope=launch%2Fpatient+openid+patient%2FPatient.rs+patient%2FCoverage.rs+patient%2FExplanationOfBenefit.rs&state=5aa4bcd8-1e7c-4c63-a366-005181d3f2b5&aud=http%3A%2F%2F192.168.0.146%3A8000%2Fv2%2Ffhir%2F&code_challenge=M3SN8Qrp0AcVsncgiQqqQWQVdptwiONbcsbBSEskIdQ&code_challenge_method=S256")
        time.sleep(5)
        driver.find_element(By.ID, "approve").click()
        time.sleep(5)
        driver.get("http://localhost/smart_stu2_2/26kuNUGB4cN#smart_stu2_2-smart_full_standalone_launch")
        time.sleep(5)
