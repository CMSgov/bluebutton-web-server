import time

from .selenium_generic import SeleniumGenericTests

from selenium.webdriver.common.by import By

USE_NEW_PERM_SCREEN = "true"


class TestInfernoSuites(SeleniumGenericTests):
    def test_inferno_suites(self):
        driver = self.driver
        driver.get("http://192.168.0.146/")
        time.sleep(5)
        driver.find_element(By.XPATH, "//*[text()='SMART App Launch STU2.2']").click()
        time.sleep(5)
        driver.find_element(By.XPATH, "//button[@type='button']").click()
        time.sleep(5)

        driver.find_element(By.XPATH, "//body").click()
        time.sleep(5)

        # More recorded and exported code from using Kataln plugin
        # Not working out of the box, need to translate into chrome webdriver calls

        # driver.find_element(By.XPATH, "//ul[@id=':r2:']/li[2]").click()
        # driver.find_element(By.XPATH, "//div[@id='root']/div/div/main/div/div/div/span[2]/button").click()
        # driver.find_element(
        # By.XPATH, "(.//*[normalize-space(text()) and normalize-space(.)='Run All Tests'])[1]//*[name()='svg'][1]").click()
        # driver.find_element_by_id("input0_text").click()
        # driver.find_element_by_id("input0_text").clear()
        # driver.find_element_by_id("input0_text").send_keys("https://test.bluebutton.cms.gov/v2/fhir/")
        # driver.find_element_by_id("input4_text").click()
        # driver.find_element_by_id("input4_text").clear()
        # driver.find_element_by_id("input4_text").send_keys("BiBafP9DlKIR6Qg3f9DTqFC5VrAK524qC3dLHmri")
        # driver.find_element_by_id("input5_text").click()
        # driver.find_element_by_id("input5_text").clear()
        # driver.find_element_by_id("input5_text").send_keys("AiXy4Gt33pgvjLrY9FPy9N7fKD9t5FoPqTdGmK72hCp4mkAYww5F39PubC4XrqFUEVrMBQbpUioWJjwiCN7i3NOIZnb3ZMynaQDs73Ezfk5kaKg63LuXmQoTdR7GTW74")
        # driver.find_element(
        # By.XPATH, "(.//*[normalize-space(text()) and normalize-space(.)='Cancel'])[1]/following::button[1]").click()
        # driver.find_element_by_link_text("Follow this link to authorize with the SMART server").click()
        # driver.get("https://test.medicare.gov/account/login/?client_id=bb2api&redirect_uri=https%3A%2F%2Ftest.bluebutton.cms.gov%2Fmymedicare%2Fsls-callback&relay=37816937312462395298185906")
        # driver.find_element_by_id("username-textbox").click()
        # driver.find_element_by_id("username-textbox").clear()
        # driver.find_element_by_id("username-textbox").send_keys("BBUser00000")
        # driver.find_element_by_id("password-textbox").click()
        # driver.find_element_by_id("password-textbox").clear()
        # driver.find_element_by_id("password-textbox").send_keys("PW00000!")
        # driver.find_element_by_id("login-button").click()
        # driver.get("https://test.bluebutton.cms.gov/v2/o/authorize/33cf71fe-7623-430c-b41a-26752221dc6f/?response_type=code&client_id=YrxYYKbqIpauLWvsfbaG7eanCnPxF9lVkGLjteiQ&redirect_uri=http%3A%2F%2Flocalhost%2Fcustom%2Fsmart_stu2_2%2Fredirect&scope=launch%2Fpatient+openid+profile+patient%2FPatient.rs&state=bd3e76cb-3c1b-487a-965f-3c90feb8f01b&aud=https%3A%2F%2Ftest.bluebutton.cms.gov%2Fv2%2Ffhir%2F&code_challenge=g9Htzf-l4E-j6vlyDsmQlllChSk931fsyF9VRyrVwL0&code_challenge_method=S256")
        # driver.find_element_by_id("approve").click()
        # driver.get("http://localhost/smart_stu2_2/87eLgdRIMaJ#smart_stu2_2")
        # driver.find_element_by_link_text("Standalone Launch").click()
