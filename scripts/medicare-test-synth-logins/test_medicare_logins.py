import argparse
import time
import signal

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from urllib3.exceptions import MaxRetryError


# CSV report at end of console out
def csv_report():
    print("#---")
    print("#---")
    print("#--- CSV REPORT ---")
    for row in report_list:
        print(f"{row[0]}, {row[1]}, {row[2]}")
    print("#---")
    print("#---")


# Handler for ctrl-c
def signal_handler(sig, frame):
    print("CTRL+c has been pressed!")
    csv_report()


signal.signal(signal.SIGINT, signal_handler)


def fail_case_mesg(s):
    match_list = [
        ["Your username or password doesn't match", "FAIL-LOGIN"],
        ["Your account needs to be updated", "FAIL-PW-EXPIRED"],
    ]

    for m in match_list:
        if m[0] in s:
            return m[1]

    return "FAIL-UNKNOWN"


def restart_selenium_driver(driver):
    driver.close()
    driver = webdriver.Chrome(options=options)
    print("# Driver restarted...")
    return driver


parser = argparse.ArgumentParser(
    description="Utility to test a medicare.gov login using Selenium"
)
parser.add_argument(
    "--url-base",
    "-u",
    help="URL Base. Default = https://www.medicare.gov",
    default="https://www.medicare.gov",
    type=str,
)
parser.add_argument(
    "--begin-user-number",
    "-b",
    help="The beginning synth account number. Ex. -b 0 for BBUser00000.",
    required=True,
    type=int,
)
parser.add_argument(
    "--end-user-number",
    "-e",
    help="The ending synth account number. Ex. -b 10 for BBUser00010.",
    required=True,
    type=int,
)
parser.add_argument(
    "--sleep-between-actions",
    "-s",
    help="Sleep time between actions. Default = 2.0",
    default=2.0,
    type=float,
)
parser.add_argument(
    "--max-retry",
    "-r",
    help="The max retry for each login attempt. Default = 3",
    default=3,
    type=int,
)
parser.add_argument(
    "--headless",
    default=False,
    action="store_true",
    help="Run in headless mode. Default = False",
)
parser.add_argument(
    "--driver-restart-count",
    "-d",
    help="Restart the driver/browser after X logins. Default = 10",
    default=10,
    type=int,
)
parser.add_argument(
    "--connection-issue-sleep",
    "-c",
    help="Sleep time when connection/network/driver issue. Default = 600",
    default=600,
    type=float,
)
parser.add_argument(
    "--max-connection-issue-count",
    "-m",
    help="Max connection issues before aborting! Default = 10",
    default=10,
    type=int,
)

args = parser.parse_args()

URL_BASE = args.url_base if args.url_base else None
BEGIN_NUM = args.begin_user_number if args.begin_user_number else None
END_NUM = args.end_user_number if args.end_user_number else None
SLEEP_BETWEEN_ACTIONS = (
    args.sleep_between_actions if args.sleep_between_actions else None
)
MAX_RETRY = args.max_retry if args.max_retry else 3
HEADLESS_MODE = args.headless if args.headless else None
DRIVER_RESTART_COUNT = args.driver_restart_count if args.driver_restart_count else None
CONNECTION_ISSUE_SLEEP = (
    args.connection_issue_sleep if args.connection_issue_sleep else None
)
MAX_CONNECTION_ISSUE_COUNT = (
    args.max_connection_issue_count if args.max_connection_issue_count else None
)

options = Options()

options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-web-security")
options.add_argument("--allow-running-insecure-content")
options.add_argument("--no-sandbox")
options.add_argument("--disable-setuid-sandbox")
options.add_argument("--disable-webgl")
options.add_argument("--disable-popup-blocking")
options.add_argument("--enable-javascript")
options.add_argument('--allow-insecure-localhost')
options.add_argument("--whitelisted-ips=''")

if HEADLESS_MODE:
    # Headless option add
    options.add_argument("--headless=new")

driver = webdriver.Chrome(options=options)

if BEGIN_NUM is None:
    BEGIN_NUM = 0

if END_NUM is None:
    END_NUM = 0

# End of run report list
report_list = []

print("# Using options: ")
print("#                Using url_base:  ", URL_BASE)
print("#   Using SLEEP_BETWEEN_ACTIONS: ", SLEEP_BETWEEN_ACTIONS)
print("#                     MAX_RETRY: ", MAX_RETRY)
print("#                 HEADLESS_MODE: ", HEADLESS_MODE)
print("#          DRIVER_RESTART_COUNT: ", DRIVER_RESTART_COUNT)
print("#        CONNECTION_ISSUE_SLEEP: ", CONNECTION_ISSUE_SLEEP)
print("#    MAX_CONNECTION_ISSUE_COUNT: ", MAX_CONNECTION_ISSUE_COUNT)
print("#")
print("# Beginning User Number: ", BEGIN_NUM)
print("#    Ending User Number: ", END_NUM)
print("#")
print("# Starting.... Press CTRL-c twice to abort.")
print("#")

driver_restart_counter = 1
connection_issue_count = 0

# Loop through synth users
for n in range(BEGIN_NUM, END_NUM + 1):

    status_mesg = "UNKNOWN"

    if driver_restart_counter % DRIVER_RESTART_COUNT == 0:
        driver = restart_selenium_driver(driver)

    username = f"BBUser{str(n).zfill(5)}"
    password = f"PW{str(n).zfill(5)}!"
    print("# ----")
    for t in range(0, MAX_RETRY):
        print(f"# TESING({t}):  n={n} username={username}")

        sleep_time = SLEEP_BETWEEN_ACTIONS * (t + 1)

        try:
            driver.get(URL_BASE + "/account/login")
            time.sleep(sleep_time)

            driver.find_element("id", "username-textbox").send_keys(username)
            driver.find_element("id", "password-textbox").send_keys(password)
            time.sleep(sleep_time)

            driver.find_element("id", "login-button").click()
            time.sleep(sleep_time)

            WebDriverWait(driver=driver, timeout=10).until(
                lambda x: x.execute_script("return document.readyState === 'complete'")
            )
            time.sleep(SLEEP_BETWEEN_ACTIONS)

            get_url = driver.current_url

            # Get page source
            ps = driver.page_source

            if "Log out" in ps:
                print("# LOGIN SUCCESSFUL!")
                status_mesg = "SUCCESS"
                print("#")
            else:
                fail_mesg = fail_case_mesg(ps)
                print("# LOGIN FAILED with: ", fail_mesg)
                status_mesg = fail_mesg
                if status_mesg == "FAIL-UNKNOWN":
                    driver.get(URL_BASE + "/sso/signout")
                    driver = restart_selenium_driver(driver)
                    time.sleep(sleep_time)
                    continue

            # Perform logout:
            driver.get(URL_BASE + "/sso/signout")
            time.sleep(sleep_time)

        except NoSuchElementException:
            # Retry
            time.sleep(sleep_time)
            continue

        except (MaxRetryError, WebDriverException):
            # Network connection issues & others.
            connection_issue_count += 1
            print("# FAIL connection issue? Sleeping for a while...")
            time.sleep(CONNECTION_ISSUE_SLEEP)
            continue

        break

    if connection_issue_count >= MAX_CONNECTION_ISSUE_COUNT:
        print("# Maximum connection issue count exceeded!!! ABORTING!")
        break

    report_list.append([URL_BASE, username, status_mesg])

    driver_restart_counter += 1

driver.quit()
csv_report()
