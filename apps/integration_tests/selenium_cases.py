import os
from enum import Enum
from selenium.webdriver.common.by import By

HOSTNAME_URL = os.environ['HOSTNAME_URL']
USE_NEW_PERM_SCREEN = os.environ['USE_NEW_PERM_SCREEN']
USE_LOGIN_WITH_MEDICARE_BUTTON = os.getenv('USE_LOGIN_WITH_MEDICARE_BUTTON', 'false')
PROD_URL = 'https://api.bluebutton.cms.gov'
USER_ACTIVATION_PATH_FMT = "{}/v1/accounts/activation-verify/{}"


class Action(Enum):
    LOAD_PAGE = 1
    FIND_CLICK = 2
    FIND = 3
    FIND_SEND_KEY = 4
    CHECK = 5
    CHECK_PKCE_CHALLENGE = 6
    BACK = 7
    LOGIN = 8
    CONTAIN_TEXT = 9
    GET_SAMPLE_TOKEN_PKCE_START = 10
    SLEEP = 11
    VALIDATE_EMAIL_NOTIFICATION = 12
    CHECK_DATE_FORMAT = 13
    COPY_LINK_AND_LOAD_WITH_PARAM = 14
    FIND_MSG_BY_CLASS = 15


MESSAGE_NO_PERMISSION = "You do not have permission to perform this action."
TESTCASE_BANNER_FMT = "** {} TEST: {}, API: {}, STEP: {}, {}"
'''
UI Widget text: texts on e.g. buttons, links, labels etc.
'''

# Synthetic beneficiary login info
BENE_TXT_USERNAME = 'BBUser09001'
BENE_TXT_PASSWORD_SBX = 'PW09001!'
BENE_TXT_PASSWORD_PROD = 'PW09001!'
BENE_TXT_PASSWORD = \
    BENE_TXT_PASSWORD_PROD if HOSTNAME_URL.startswith(PROD_URL) else BENE_TXT_PASSWORD_SBX

LNK_TXT_SIGNUP = "Signup"
TAG_FOR_AUTHORIZE_LINK = "pre"
# FHIR search result bundle pagination
FHIR_LNK_TXT_NAV_FIRST = "first"
FHIR_LNK_TXT_NAV_NEXT = "next"
FHIR_LNK_TXT_NAV_PREV = "previous"
FHIR_LNK_TXT_NAV_LAST = "last"
FHIR_LNK_TXT_NAV_SELF = "self"
# FHIR resources query page
FHIR_LNK_TXT_PATIENT = "Patient"
FHIR_LNK_TXT_EOB = "ExplanationOfBenefit"
FHIR_LNK_TXT_COVERAGE = "Coverage"
FHIR_LNK_TXT_PROFILE = "Profile"
FHIR_LNK_TXT_METADATA = "FHIR Metadata"
FHIR_LNK_TXT_OIDC_DISCOVERY = "OIDC Discovery"
FHIR_LNK_TXT_DIGITAL_INSURANCE_CARD = "Digital Insurance Card"
# Spanish-English toggle link
LNK_TXT_SPANISH = "Cambiar a español"
LNK_TXT_ENGLISH = "Change to English"
# FHIR result page label H2
LAB_FHIR_RESULTPAGE_H2 = "h2"
CONTENT_FHIR_RESULTPAGE_PRE = "pre"
FHIR_RESULT_BTN_COPY = 'bb-copy-button'

# MSLSX login form
MSLSX_TXT_FLD_USERNAME = "username"
MSLSX_TXT_FLD_HICN = "hicn"
MSLSX_TXT_FLD_MBI = "mbi"
MSLSX_TXT_FLD_USERNAME_VAL = BENE_TXT_USERNAME
MSLSX_TXT_FLD_HICN_VAL = "00000000000"
MSLSX_TXT_FLD_MBI_VAL = "1S00EU8DG39"
MSLSX_BTN_SUBMIT = "button"

# MSLSX login Fred
MSLSX_TXT_FLD_FRED_USERNAME_VAL = 'rogersf'
MSLSX_TXT_FLD_FRED_HICN_VAL = '1000044680'
MSLSX_TXT_FLD_FRED_MBI_VAL = '2SW4N00AA00'

# Home page
HOME_LNK_TXT_TESTCLIENT = "Test Client"

# TestClient
TESTCLIENT_BTN_GET_TOKEN_V2 = "Get a Sample Authorization Token"
TESTCLIENT_BTN_GET_TOKEN_V3 = "Get a Sample Authorization Token v3"
TESTCLIENT_BTN_AUTH_AS_BENE_ENGLISH = "Authorize as a Beneficiary"
TESTCLIENT_BTN_AUTH_AS_BENE_SPANISH = "Authorize as a Beneficiary (Spanish)"
TESTCLIENT_LNK_TXT_RESTART = "restart testclient"
TESTCLIENT_BUNDLE_LABEL_FMT = "Response (Bundle of {}), API version: {}"
TESTCLIENT_RESOURCE_LABEL_FMT = "Response ({}), API version: {}"

# email notification subjects
USER_ACCT_ACTIVATION_EMAIL_SUBJ = "Subject: Verify Your Blue Button 2.0 Developer Sandbox Account"
USER_ACCT_1ST_APP_EMAIL_SUBJ = "Subject: Congrats on Registering Your First Application!"
USER_ACCT_ACTIVATION_KEY_PREFIX = 'title="Verify Your Email"'
APP_1ST_API_CALL_EMAIL_SUBJ = "Subject: Congrats on Making Your First API Call"

# create user account form fields
USER_TXT_FLD_ID_FNAME = "id_first_name"
USER_TXT_FLD_ID_LNAME = "id_last_name"
USER_TXT_FLD_ID_EMAIL = "id_email"
USER_TXT_FLD_ID_ORG_NAME = "id_organization_name"
USER_TXT_FLD_ID_PASSWD1 = "id_password1"
USER_TXT_FLD_ID_PASSWD2 = "id_password2"
USER_FORM_SUBMIT_BTN = ".ds-c-button"
USER_TXT_FLD_ID_FNAME_VAL = "fn_test_user_001"
USER_TXT_FLD_ID_LNAME_VAL = "ln_test_user_001"
USER_TXT_FLD_ID_EMAIL_VAL = "test_user_001@xyz.net"
USER_TXT_FLD_ID_ORG_NAME_VAL = "XYZ Inc"
USER_TXT_FLD_ID_PASSWD1_VAL = "BlueTest1234567890@Local"
USER_TXT_FLD_ID_PASSWD2_VAL = "BlueTest1234567890@Local"
USER_SBX_LOGIN_TITLE = "Sandbox Login"
USER_SBX_LOGIN_TITLE_H1 = "h1"

# user login form
USER_LOGIN_USERNAME = "id_username"
USER_LOGIN_PASSWORD = "id_password"
USER_LOGIN_USERNAME_VAL = "test_user_001@xyz.net"
USER_LOGIN_PASSWORD_VAL = "BlueTest1234567890@Local"
USER_LOGIN_BTN = ".ds-c-button"
USER_LOGIN_MSG_ID = "messages"
USER_ACCT_CREATED_MSG = "Your account was created. Please check your email to verify your account before logging in."
USER_ACCT_ACTIVATED_MSG = "Your account has been activated. You may now login."
USER_NOT_ACTIVE_ALERT_MSG = "Please click the verification link in your email before logging in."
USER_ACTIVATE_BAD_KEY_MSG = "There may be an issue with your account. Contact us at bluebuttonapi@cms.hhs.gov"
USER_LNK_TXT_ACCT_LOGOUT = "Logout"

# language and localization checking
AUTH_SCREEN_ID_LANG = "connect_app"
AUTH_SCREEN_ID_END_DATE = "permission_end_date"
AUTH_SCREEN_ID_EXPIRE_INFO = "permission_expire_info"
AUTH_SCREEN_ES_TXT = "Desea compartir sus datos de Medicare"
AUTH_SCREEN_EN_TXT = "Connect your Medicare claims"
AUTH_SCREEN_EN_EXPIRE_INFO_TXT = "TestApp will have access to your data for 13 months, until"
AUTH_SCREEN_ES_EXPIRE_INFO_TXT = "TestApp tendrá acceso a sus datos durante 13 meses, hasta el"
# regex for date formats
AUTH_SCREEN_ES_DATE_FORMAT = "^(?P<day>\\d{1,2}) de (?P<month>\\w+) de (?P<year>\\d{4})"
# Django en locale date format is 3 letter abbrev plus period or full month name (e.g. March, May)
AUTH_SCREEN_EN_DATE_FORMAT = "^(?P<month>\\w{3,4}\\.|\\w+) (?P<day>\\d{1,2}), (?P<year>\\d{4})"
SLSX_LOGIN_BUTTON_SPANISH = "Entrar"

# app form
LNK_TXT_APP_ADD = "Add an Application"
APP_ID_NAME = "id_name"
APP_ID_REDIRECT_URIS = "id_redirect_uris"
APP_ID_AGREE = "id_agree"
APP_ID_LOGO_IMG = "id_logo_image"
APP_ID_NAME_VAL = "My_Sample_App"
APP_ID_REDIRECT_URIS_VAL = "http://localhost:3001/api/bluebutton/callback/"
APP_ID_LOGO_IMG_VAL = "C:\\fakepath\\LogoMakr_apple.jpg"
APP_CSS_CLASS_DEMO_YES = ".ds-c-fieldset > label:nth-child(3)"
APP_CSS_CLASS_SAVE_APP = ".ds-c-button--success"
APP_LNK_TXT_BACK_TO_DASHBOARD = "Back to Dashboard"
APP_CSS_SELECTOR_EDIT_APP = ".cta-button:nth-child(1)"
APP_CSS_SELECTOR_DELETE_APP = ".cta-button:nth-child(2)"

# SLSX login form
SLSX_TXT_FLD_USERNAME = 'username'
SLSX_TXT_FLD_PASSWORD = 'password'
SLSX_TXT_FLD_USERNAME_VAL = BENE_TXT_USERNAME
SLSX_TXT_FLD_PASSWORD_VAL = BENE_TXT_PASSWORD
SLSX_CSS_BUTTON = "login-button"
SLSX_CSS_CONTINUE_BUTTON = "button[type='submit']"
SLSX_CSS_LOGIN_BUTTON = "//button[@type='submit' and (normalize-space(text())='Log in' or normalize-space(text())='Entrar')]"

# Demographic info access grant form
BTN_ID_GRANT_DEMO_ACCESS = "approve"
BTN_ID_DENY_DEMO_ACCESS = "deny"
BTN_ID_RADIO_NOT_SHARE = "radio_1" if USE_NEW_PERM_SCREEN == "true" else "label:nth-child(5)"

# Supported Locale
EN_US = "en_us"
ES_ES = "es_es"

# v2 SMART APP scope constants
X_PATH_FOR_USER_SCOPES = "//*[@id='main-content']/div/div/div/pre"
COVERAGE_SCOPE = "patient/Coverage.rs"
PATIENT_SCOPE = "patient/Patient.rs"
EOB_SCOPE = "patient/ExplanationOfBenefit.rs"
OPENID_SCOPE = "openid"
LAUNCH_SCOPE = "launch/patient"

BROWSERBACK = {
    "display": "Back to FHIR resource page",
    "action": Action.BACK,
}

WAIT_SECONDS = {
    "display": "Sleep seconds...",
    "action": Action.SLEEP,
    "params": [2],
}

CHECK_TESTCLIENT_START_PAGE = {
    "display": "Check it's on 'Test Client' start page",
    "action": Action.FIND,
    "params": [30, By.LINK_TEXT, TESTCLIENT_BTN_GET_TOKEN_V2]
}

CLICK_TESTCLIENT = {
    "display": "Click link 'Test Client'",
    "action": Action.FIND_CLICK,
    "params": [30, By.LINK_TEXT, HOME_LNK_TXT_TESTCLIENT]
}

CLICK_RESTART_TESTCLIENT = {
    "display": "Click link 'restart testclient'",
    "action": Action.FIND_CLICK,
    "params": [30, By.LINK_TEXT, TESTCLIENT_LNK_TXT_RESTART]
}

LOAD_TESTCLIENT_HOME = {
    "display": "Load Test Client Home Page",
    "action": Action.LOAD_PAGE,
    "params": [HOSTNAME_URL + "/testclient"]
}

CLICK_RADIO_NOT_SHARE = {
    "display": "Click 'Share healthcare data, but not your personal info' on DEMO info grant form",
    "action": Action.FIND_CLICK,
    # Below works for old auth screen
    "params": [20, By.CSS_SELECTOR, BTN_ID_RADIO_NOT_SHARE]
}

CLICK_RADIO_NOT_SHARE_NEW_PERM_SCREEN = {
    "display": "Click 'Share healthcare data, but not your personal info' on DEMO info grant form (NEW PERM SCREEN)",
    "action": Action.FIND_CLICK,
    # Below works for new auth screen
    "params": [20, By.ID, BTN_ID_RADIO_NOT_SHARE]
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

CLICK_SPANISH = {
    "display": "Click Spanish language link",
    "action": Action.FIND_CLICK,
    "params": [20, By.LINK_TEXT, LNK_TXT_SPANISH]
}

CLICK_ENGLISH = {
    "display": "Click English language link",
    "action": Action.FIND_CLICK,
    "params": [20, By.LINK_TEXT, LNK_TXT_ENGLISH]
}

CALL_LOGIN = {
    "display": "Start login ...",
    "action": Action.LOGIN,
}

# Navigate back to TestClient home page, different between prod and test/sbx/local
TESTCLIENT_HOME = [
    WAIT_SECONDS,
    CLICK_TESTCLIENT if not HOSTNAME_URL.startswith(PROD_URL) else LOAD_TESTCLIENT_HOME,
    WAIT_SECONDS
]

# MSLSX login using BBUser09001
SEQ_LOGIN_MSLSX = [
    {
        "display": "Input SUB(username)",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, MSLSX_TXT_FLD_USERNAME, MSLSX_TXT_FLD_USERNAME_VAL]
    },
    {
        "display": "Input hicn",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, MSLSX_TXT_FLD_HICN, MSLSX_TXT_FLD_HICN_VAL]
    },
    {
        "display": "Input mbi",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, MSLSX_TXT_FLD_MBI, MSLSX_TXT_FLD_MBI_VAL]
    },
    {
        "display": "Click 'submit' on MSLSX login form",
        "action": Action.FIND_CLICK,
        "params": [20, By.CSS_SELECTOR, MSLSX_BTN_SUBMIT]
    },
]

# MSLSX login, but using the Fred super user (currently unused)
SEQ_LOGIN_MSLSX_FRED = [
    {
        "display": "Input SUB(username)",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, MSLSX_TXT_FLD_USERNAME, MSLSX_TXT_FLD_FRED_USERNAME_VAL]
    },
    {
        "display": "Input hicn",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, MSLSX_TXT_FLD_HICN, MSLSX_TXT_FLD_FRED_HICN_VAL]
    },
    {
        "display": "Input mbi",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, MSLSX_TXT_FLD_MBI, MSLSX_TXT_FLD_FRED_MBI_VAL]
    },
    {
        "display": "Click 'submit' on MSLSX login form",
        "action": Action.FIND_CLICK,
        "params": [20, By.CSS_SELECTOR, MSLSX_BTN_SUBMIT]
    },
]

LOGIN_WITH_MEDICARE_BUTTON_SETUP = []
if USE_LOGIN_WITH_MEDICARE_BUTTON == 'true':
    LOGIN_WITH_MEDICARE_BUTTON_SETUP = [{
        "display": "Click 'Log in with Medicare.gov' button",
        "action": Action.FIND_CLICK,
        "params": [
            20,
            By.CSS_SELECTOR,
            "button.ds-c-button.ds-c-button--solid.ds-u-margin-top--2"
        ],
    }]

# SLSX login using BBUser09001
SEQ_LOGIN_SLSX = LOGIN_WITH_MEDICARE_BUTTON_SETUP + [

    {
        "display": "Medicare.gov login username",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, SLSX_TXT_FLD_USERNAME, SLSX_TXT_FLD_USERNAME_VAL]
    },
    {
        "display": "Click 'Continue' on SLSX login form",
        "action": Action.FIND_CLICK,
        "params": [20, By.CSS_SELECTOR, SLSX_CSS_CONTINUE_BUTTON]
    },
    WAIT_SECONDS,
    {
        "display": "Medicare.gov login password",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, SLSX_TXT_FLD_PASSWORD, SLSX_TXT_FLD_PASSWORD_VAL]
    },
    {
        "display": "Click 'Log In' on SLSX login form",
        "action": Action.FIND_CLICK,
        "params": [20, By.XPATH, SLSX_CSS_LOGIN_BUTTON]
    },
    WAIT_SECONDS
]

SEQ_REACH_AUTHORIZE_BTN = [
    {
        "display": "Load BB2 Landing Page ...",
        "action": Action.LOAD_PAGE,
        "params": [HOSTNAME_URL]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click link to get sample token v1/v2 with PKCE enabled",
        "action": Action.GET_SAMPLE_TOKEN_PKCE_START,
    },
]

SEQ_AUTHORIZE_START_SPANISH = [
    {"sequence": SEQ_REACH_AUTHORIZE_BTN},
    {
        "display": "Check authorize link for PKCE challenge info present",
        "action": Action.CHECK_PKCE_CHALLENGE,
        "params": [20, By.TAG_NAME, TAG_FOR_AUTHORIZE_LINK, True]
    },
    {
        "display": "Click link 'Authorize as a Beneficiary (Spanish)' - start authorization using medicare login in Spanish",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, TESTCLIENT_BTN_AUTH_AS_BENE_SPANISH]
    },
]

SEQ_AUTHORIZE_RESTART = [
    CLICK_RESTART_TESTCLIENT,
    {
        "display": "Click link to get sample token v1/v2",
        "action": Action.GET_SAMPLE_TOKEN_PKCE_START,
    },
    {
        "display": "Click link 'Authorize as a Beneficiary' - start authorization",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, TESTCLIENT_BTN_AUTH_AS_BENE_ENGLISH]
    },
]

SEQ_AUTHORIZE_PKCE_START = [
    {"sequence": SEQ_REACH_AUTHORIZE_BTN},
    {
        "display": "Check authorize link for PKCE challenge info present",
        "action": Action.CHECK_PKCE_CHALLENGE,
        "params": [20, By.TAG_NAME, TAG_FOR_AUTHORIZE_LINK, True]
    },
    {
        "display": "Click link 'Authorize as a Beneficiary' - start authorization",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, TESTCLIENT_BTN_AUTH_AS_BENE_ENGLISH]
    },
]

SEQ_AUTHORIZE_LANG_PARAM_START = [
    {
        "display": "Load BB2 Landing Page ...",
        "action": Action.LOAD_PAGE,
        "params": [HOSTNAME_URL]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click link to get sample token v1/v2",
        "action": Action.GET_SAMPLE_TOKEN_PKCE_START,
    },
    {
        "display": "Call authorize endpoint with lang param - start authorization",
        "action": Action.COPY_LINK_AND_LOAD_WITH_PARAM,
        "params": [30, By.LINK_TEXT, TESTCLIENT_BTN_AUTH_AS_BENE_ENGLISH]
    },
]

SEQ_QUERY_FHIR_RESOURCES_V2 = [
    {
        "display": "Click 'Patient' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_PATIENT]
    },
    {
        "display": "Check Patient result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_TXT_PATIENT]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'Coverage' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_COVERAGE]
    },
    {
        "display": "Check Coverage result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, FHIR_LNK_TXT_COVERAGE]
    },
    {
        "display": "Check and click Coverage result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_NAV_LAST]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'ExplanationOfBenefit' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_EOB]
    },
    {
        "display": "Check ExplanationOfBenefit result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, FHIR_LNK_TXT_EOB]
    },
    {
        "display": "Check and click ExplanationOfBenefit result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_NAV_LAST]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'Profile' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_PROFILE]
    },
    WAIT_SECONDS,
    {
        "display": "Check Profile result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT,
                   f'{FHIR_LNK_TXT_PROFILE} (OIDC Userinfo)']
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'FHIR Metadata' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_METADATA]
    },
    {
        "display": "Check FHIR Metadata result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_TXT_METADATA]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'OIDC Discovery' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_OIDC_DISCOVERY]
    },
    {
        "display": "Check OIDC Discovery result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_TXT_OIDC_DISCOVERY]
    },
    TESTCLIENT_HOME,
]

SEQ_QUERY_FHIR_RESOURCES_V3 = SEQ_QUERY_FHIR_RESOURCES_V2 + [
    {
        "display": "Click 'Digital Insurance Card' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_PATIENT]
    },
]

SEQ_QUERY_FHIR_RESOURCES_NO_DEMO = [
    {
        "display": "Click 'Patient' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_PATIENT]
    },
    {
        "display": "Check Patient result page content (<pre>) expect no permission message",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.TAG_NAME, CONTENT_FHIR_RESULTPAGE_PRE, MESSAGE_NO_PERMISSION]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'Coverage' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_COVERAGE]
    },
    {
        "display": "Check Coverage result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, FHIR_LNK_TXT_COVERAGE]
    },
    {
        "display": "Check and click Coverage result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_NAV_LAST]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'ExplanationOfBenefit' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_EOB]
    },
    {
        "display": "Check ExplanationOfBenefit result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, FHIR_LNK_TXT_EOB]
    },
    {
        "display": "Check and click ExplanationOfBenefit result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_NAV_LAST]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'Profile' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_PROFILE]
    },
    WAIT_SECONDS,
    {
        "display": "Check Profile result page content (<pre>) expect no permission message",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.TAG_NAME, CONTENT_FHIR_RESULTPAGE_PRE, MESSAGE_NO_PERMISSION]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'FHIR Metadata' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_METADATA]
    },
    {
        "display": "Check FHIR Metadata result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_TXT_METADATA]
    },
    TESTCLIENT_HOME,
    {
        "display": "Click 'OIDC Discovery' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, FHIR_LNK_TXT_OIDC_DISCOVERY]
    },
    {
        "display": "Check OIDC Discovery result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, FHIR_LNK_TXT_OIDC_DISCOVERY]
    },
    TESTCLIENT_HOME,
]

SEQ_CHECK_SCOPES = [
    {
        "display": "Check that v2 SMART APP scopes were returned",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.XPATH, X_PATH_FOR_USER_SCOPES, COVERAGE_SCOPE]
    },
    {
        "display": "Check that v2 SMART APP scopes were returned",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.XPATH, X_PATH_FOR_USER_SCOPES, PATIENT_SCOPE]
    },
    {
        "display": "Check that v2 SMART APP scopes were returned",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.XPATH, X_PATH_FOR_USER_SCOPES, EOB_SCOPE]
    },
    {
        "display": "Check that v2 SMART APP scopes were returned",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.XPATH, X_PATH_FOR_USER_SCOPES, OPENID_SCOPE]
    },
    {
        "display": "Check that v2 SMART APP scopes were returned",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.XPATH, X_PATH_FOR_USER_SCOPES, LAUNCH_SCOPE]
    }
]

TESTS = {
    "auth_grant_fhir_calls_v2": [
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        CLICK_AGREE_ACCESS,
        {"sequence": SEQ_QUERY_FHIR_RESOURCES_V2}
    ],
    "auth_grant_fhir_calls_v3": [
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        CLICK_AGREE_ACCESS,
        {"sequence": SEQ_QUERY_FHIR_RESOURCES_V3}
    ],
    "auth_deny_fhir_calls": [
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        CLICK_DENY_ACCESS,
        CHECK_TESTCLIENT_START_PAGE
    ],
    "auth_grant_w_no_demo": [
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        CLICK_RADIO_NOT_SHARE,
        CLICK_AGREE_ACCESS,
        {"sequence": SEQ_QUERY_FHIR_RESOURCES_NO_DEMO}
    ],
    "auth_grant_w_no_demo_new_perm_screen": [
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        CLICK_RADIO_NOT_SHARE_NEW_PERM_SCREEN,
        CLICK_AGREE_ACCESS,
        {"sequence": SEQ_QUERY_FHIR_RESOURCES_NO_DEMO}
    ],
    "authorize_lang_english_button": [
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        WAIT_SECONDS,
        WAIT_SECONDS,
        # check the title
        {
            "display": "Check for authorization screen language in English",
            "action": Action.CONTAIN_TEXT,
            "params": [20, By.ID, AUTH_SCREEN_ID_LANG, AUTH_SCREEN_EN_TXT]
        },
        # now check the expiration info section
        {
            "display": "Check for authorization screen expire info in English",
            "action": Action.CONTAIN_TEXT,
            "params": [20, By.ID, AUTH_SCREEN_ID_EXPIRE_INFO, AUTH_SCREEN_EN_EXPIRE_INFO_TXT]
        },
        {
            "display": "Check en_US date format and validate",
            "action": Action.CHECK_DATE_FORMAT,
            "params": [20, By.ID, AUTH_SCREEN_ID_END_DATE, AUTH_SCREEN_EN_DATE_FORMAT, EN_US]
        },
        # the 'approve' and 'deny' button click not using locale based text
        # so it is lang agnostic
        CLICK_AGREE_ACCESS
    ],
    "authorize_get_v2_scopes": [
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        WAIT_SECONDS,
        WAIT_SECONDS,
        CLICK_AGREE_ACCESS,
        # Check the different scopes that have been returned
        {"sequence": SEQ_CHECK_SCOPES}
    ]
}

SPANISH_TESTS = {
    "toggle_language": [
        # kick off default test client
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        # Wait to make sure we're logged in because login page also has Spanish link
        WAIT_SECONDS,
        WAIT_SECONDS,
        CLICK_SPANISH,
        {
            "display": "Check for language change to Spanish",
            "action": Action.CONTAIN_TEXT,
            "params": [20, By.ID, AUTH_SCREEN_ID_LANG, AUTH_SCREEN_ES_TXT]
        },
        CLICK_ENGLISH,
        {
            "display": "Check for language change to English",
            "action": Action.CONTAIN_TEXT,
            "params": [20, By.ID, AUTH_SCREEN_ID_LANG, AUTH_SCREEN_EN_TXT]
        },
        {
            "display": "Check for authorization screen access grant expire info in English",
            "action": Action.CONTAIN_TEXT,
            "params": [20, By.ID, AUTH_SCREEN_ID_EXPIRE_INFO, AUTH_SCREEN_EN_EXPIRE_INFO_TXT]
        },
        {
            "display": "Check English date format and validate",
            "action": Action.CHECK_DATE_FORMAT,
            "params": [20, By.ID, AUTH_SCREEN_ID_END_DATE, AUTH_SCREEN_EN_DATE_FORMAT, EN_US]
        },
        CLICK_AGREE_ACCESS
    ],
    "authorize_lang_param": [
        # direct medicare login by inject a lang=es at the end of the url
        {"sequence": SEQ_AUTHORIZE_LANG_PARAM_START},
        {
            "display": "Check for Medicare.gov login page already in Spanish",
            "action": Action.CONTAIN_TEXT,
            "params": [20, By.ID, SLSX_CSS_BUTTON, SLSX_LOGIN_BUTTON_SPANISH]
        },
        # note, for now CALL_LOGIN does not use locale based text to look up elements
        # so it is lang agnostic
        CALL_LOGIN,
        WAIT_SECONDS,
        WAIT_SECONDS,
        # check the title
        {
            "display": "Check for authorization screen language already in Spanish",
            "action": Action.CONTAIN_TEXT,
            "params": [20, By.ID, AUTH_SCREEN_ID_LANG, AUTH_SCREEN_ES_TXT]
        },
        # now check the expiration info section
        # comment out due to on PROD TestApp is RESEARCH_STUDY which does not have expire info
        # {
        #     "display": "Check for authorization screen expire info in Spanish",
        #     "action": Action.CONTAIN_TEXT,
        #     "params": [20, By.ID, AUTH_SCREEN_ID_EXPIRE_INFO, AUTH_SCREEN_ES_EXPIRE_INFO_TXT]
        # },
        # {
        #     "display": "Check Spanish date format and validate",
        #     "action": Action.CHECK_DATE_FORMAT,
        #     "params": [20, By.ID, AUTH_SCREEN_ID_END_DATE, AUTH_SCREEN_ES_DATE_FORMAT, ES_ES]
        # },
        # the 'approve' and 'deny' button click not using locale based text
        # so it is lang agnostic
        CLICK_AGREE_ACCESS
    ],
    "authorize_lang_spanish_button": [
        {"sequence": SEQ_AUTHORIZE_START_SPANISH},
        # note, CALL_LOGIN does not use locale based text to look up elements
        # so it is lang agnostic
        CALL_LOGIN,
        WAIT_SECONDS,
        WAIT_SECONDS,
        # check the title
        {
            "display": "Check for authorization screen language already in Spanish",
            "action": Action.CONTAIN_TEXT,
            "params": [20, By.ID, AUTH_SCREEN_ID_LANG, AUTH_SCREEN_ES_TXT]
        },
        # now check the expiration info section
        # {
        #     "display": "Check for authorization screen expire info in Spanish",
        #     "action": Action.CONTAIN_TEXT,
        #     "params": [20, By.ID, AUTH_SCREEN_ID_EXPIRE_INFO, AUTH_SCREEN_ES_EXPIRE_INFO_TXT]
        # },
        # {
        #     "display": "Check Spanish date format and validate",
        #     "action": Action.CHECK_DATE_FORMAT,
        #     "params": [20, By.ID, AUTH_SCREEN_ID_END_DATE, AUTH_SCREEN_ES_DATE_FORMAT, ES_ES]
        # },
        # the 'approve' and 'deny' button click not using locale based text
        # so it is lang agnostic
        CLICK_AGREE_ACCESS
    ]
}

SEQ_CREATE_USER_ACCOUNT = [
    {
        "display": "Load BB2 Landing Page ...",
        "action": Action.LOAD_PAGE,
        "params": [HOSTNAME_URL]
    },
    {
        "display": "Click link 'Signup' to create user account",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, LNK_TXT_SIGNUP]
    },
    {
        "display": "Type in First Name...",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, USER_TXT_FLD_ID_FNAME, USER_TXT_FLD_ID_FNAME_VAL]
    },
    {
        "display": "Type in Last Name...",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, USER_TXT_FLD_ID_LNAME, USER_TXT_FLD_ID_LNAME_VAL]
    },
    {
        "display": "Type in EMAIL...",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, USER_TXT_FLD_ID_EMAIL, USER_TXT_FLD_ID_EMAIL_VAL]
    },
    {
        "display": "Type in Organization Name...",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, USER_TXT_FLD_ID_ORG_NAME, USER_TXT_FLD_ID_ORG_NAME_VAL]
    },
    {
        "display": "Type in Password...",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, USER_TXT_FLD_ID_PASSWD1, USER_TXT_FLD_ID_PASSWD1_VAL]
    },
    {
        "display": "Type in Password again to confirm...",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, USER_TXT_FLD_ID_PASSWD2, USER_TXT_FLD_ID_PASSWD2_VAL]
    },
    {
        "display": "Click link submit button",
        "action": Action.FIND_CLICK,
        "params": [30, By.CSS_SELECTOR, USER_FORM_SUBMIT_BTN]
    },
]

SEQ_USER_LOGIN = [
    {
        "display": "Type in user name (email)...",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, USER_LOGIN_USERNAME, USER_LOGIN_USERNAME_VAL]
    },
    {
        "display": "Type in Password...",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, USER_LOGIN_PASSWORD, USER_LOGIN_PASSWORD_VAL]
    },
    {
        "display": "Click login button",
        "action": Action.FIND_CLICK,
        "params": [30, By.CSS_SELECTOR, USER_LOGIN_BTN]
    },
]

SEE_ACCT_CREATED_MSG = {
    "display": "Check new user login prompt message shown up...",
    "action": Action.CONTAIN_TEXT,
    "params": [20, By.ID, USER_LOGIN_MSG_ID, USER_ACCT_CREATED_MSG]
}

SEE_ACCT_ACTIVATED_MSG = {
    "display": "Check account activated and you can login now message shown...",
    "action": Action.CONTAIN_TEXT,
    "params": [20, By.ID, USER_LOGIN_MSG_ID, USER_ACCT_ACTIVATED_MSG]
}

VALIDATE_ACTIVATION_EMAIL = {
    "display": "Check BB2 server log for user account activation email and activate account",
    "action": Action.VALIDATE_EMAIL_NOTIFICATION,
    "params": [USER_ACCT_ACTIVATION_EMAIL_SUBJ, USER_ACCT_ACTIVATION_KEY_PREFIX]
}

VALIDATE_1ST_APP_CREATED_EMAIL = {
    "display": "Check BB2 server log for email notification of 1st app created",
    "action": Action.VALIDATE_EMAIL_NOTIFICATION,
    "params": [USER_ACCT_1ST_APP_EMAIL_SUBJ, None]
}

VALIDATE_1ST_API_CALL_EMAIL = {
    "display": "Check BB2 server log for email notification of 1st API call",
    "action": Action.VALIDATE_EMAIL_NOTIFICATION,
    "params": [APP_1ST_API_CALL_EMAIL_SUBJ, None]
}

USER_ACCT_LOGOUT = {
    "display": "Find and click the link 'Logout'...",
    "action": Action.FIND_CLICK,
    "params": [20, By.LINK_TEXT, USER_LNK_TXT_ACCT_LOGOUT]
}

SEQ_ADD_APPS = [
    {
        "display": "Click 'Add an Application'...",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_APP_ADD]
    },
    {
        "display": "Type in app name...",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, APP_ID_NAME, APP_ID_NAME_VAL]
    },
    {
        "display": "Type in redirect URI...",
        "action": Action.FIND_SEND_KEY,
        "params": [30, By.ID, APP_ID_REDIRECT_URIS, APP_ID_REDIRECT_URIS_VAL]
    },
    {
        "display": "Select radio button 'Yes' to collect demographic info...",
        "action": Action.FIND_CLICK,
        "params": [30, By.CSS_SELECTOR, APP_CSS_CLASS_DEMO_YES]
    },
    {
        "display": "Check term of service check box (Yes)...",
        "action": Action.FIND_CLICK,
        "params": [30, By.ID, APP_ID_AGREE]
    },
    {
        "display": "Click 'Save Application' button...",
        "action": Action.FIND_CLICK,
        "params": [30, By.CSS_SELECTOR, APP_CSS_CLASS_SAVE_APP]
    },
    VALIDATE_1ST_APP_CREATED_EMAIL,
    {
        "display": "Click 'Back to Dashboard' link..., to add 2nd app",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, APP_LNK_TXT_BACK_TO_DASHBOARD]
    },
    {
        "display": "Click 'Add an Application'..., 2nd app",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_APP_ADD]
    },
    {
        "display": "Type in app name..., 2nd app",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, APP_ID_NAME, APP_ID_NAME_VAL + "_2ND"]
    },
    {
        "display": "Type in redirect URI..., 2nd app",
        "action": Action.FIND_SEND_KEY,
        "params": [30, By.ID, APP_ID_REDIRECT_URIS, APP_ID_REDIRECT_URIS_VAL + "for_2nd_app/"]
    },
    {
        "display": "Select radio button 'Yes' to collect demographic info..., 2nd app",
        "action": Action.FIND_CLICK,
        "params": [30, By.CSS_SELECTOR, APP_CSS_CLASS_DEMO_YES]
    },
    {
        "display": "Check term of service check box (Yes)..., 2nd app",
        "action": Action.FIND_CLICK,
        "params": [30, By.ID, APP_ID_AGREE]
    },
    {
        "display": "Click 'Save Application' button..., 2nd app",
        "action": Action.FIND_CLICK,
        "params": [30, By.CSS_SELECTOR, APP_CSS_CLASS_SAVE_APP]
    },
    {
        "display": "Click 'Back to Dashboard' link..., to add 2nd app",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, APP_LNK_TXT_BACK_TO_DASHBOARD]
    },
    VALIDATE_1ST_APP_CREATED_EMAIL,
]

SEQ_UPD_APPS = [
    {
        "display": "Find and click the link 'My_Sample_App'...",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, APP_ID_NAME_VAL]
    },
    {
        "display": "At App view for 'My_Sample_App', Click: 'Edit Application'...",
        "action": Action.FIND_CLICK,
        "params": [20, By.CSS_SELECTOR, APP_CSS_SELECTOR_EDIT_APP]
    },
    {
        "display": "Type in app name changed...",
        "action": Action.FIND_SEND_KEY,
        "params": [30, By.ID, APP_ID_NAME, "_UPDATED"]
    },
    {
        "display": "Click 'Save Application' button...",
        "action": Action.FIND_CLICK,
        "params": [30, By.CSS_SELECTOR, APP_CSS_CLASS_SAVE_APP]
    },
    {
        "display": "Check current app name present as 'My_Sample_App_UPDATED'",
        "action": Action.CONTAIN_TEXT,
        "params": [30, By.TAG_NAME, "h1", APP_ID_NAME_VAL + "_UPDATED"]
    },
    {
        "display": "Click 'Back to Dashboard' link..., to all apps view",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, APP_LNK_TXT_BACK_TO_DASHBOARD]
    },
]

SEQ_DEL_APPS = [
    {
        "display": "Find and click the link 'My_Sample_App_UPDATED'...",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, APP_ID_NAME_VAL + "_UPDATED"]
    },
    {
        "display": "At App view for 'My_Sample_App_UPDATED', Click: 'Delete Application'...",
        "action": Action.FIND_CLICK,
        "params": [20, By.CSS_SELECTOR, APP_CSS_SELECTOR_DELETE_APP]
    },
    {
        "display": "Confirm by click 'Delete' button when asked 'Are you sure you want to delete ...'",
        "action": Action.FIND_CLICK,
        "params": [30, By.NAME, "allow"]
    },
    WAIT_SECONDS,
    {
        "display": "Check we are back to the all app view...",
        "action": Action.CONTAIN_TEXT,
        "params": [30, By.TAG_NAME, "h1", "Developer Dashboard"]
    },
]

USER_ACCT_ACTIVATION_W_BAD_KEY = {
    "display": "Send activation request (with bad activation key)...",
    "action": Action.LOAD_PAGE,
    "params": [USER_ACTIVATION_PATH_FMT.format(HOSTNAME_URL, "bad-key-470c74445228")]
}

SEE_ACCOUNT_HAS_ISSUE_MSG = {
    "display": "Check error message present (There may be an issue with your account. Contact us at..)",
    "action": Action.CONTAIN_TEXT,
    "params": [20, By.ID, "messages", USER_ACTIVATE_BAD_KEY_MSG]
}

SEE_LOGIN_BEFORE_ACTIVATION_MSG = {
    "display": "Check login without activation error message present...",
    "action": Action.CONTAIN_TEXT,
    # TODO: use other xpath than class which is sensitive to changes
    "params": [20, By.XPATH, "//div[@class='alert alert-danger alert-dismissible']", USER_NOT_ACTIVE_ALERT_MSG]
}

# Test user creation, activation, login, logout, app registration / modification / deletion
ACCT_TESTS = {
    "create_user_account": [
        {"sequence": SEQ_CREATE_USER_ACCOUNT},
        WAIT_SECONDS,
        WAIT_SECONDS,
        SEE_ACCT_CREATED_MSG,
        {"sequence": SEQ_USER_LOGIN},
        WAIT_SECONDS,
        WAIT_SECONDS,
        SEE_LOGIN_BEFORE_ACTIVATION_MSG,
        WAIT_SECONDS,
    ],
    "validate_activation_key_err_msg": [
        USER_ACCT_ACTIVATION_W_BAD_KEY,
        SEE_ACCOUNT_HAS_ISSUE_MSG,
        WAIT_SECONDS,
    ],
    "login_user_account_add_app": [
        SEE_ACCT_ACTIVATED_MSG,
        {"sequence": SEQ_USER_LOGIN},
        {"sequence": SEQ_ADD_APPS},
        {"sequence": SEQ_UPD_APPS},
        {"sequence": SEQ_DEL_APPS},
        WAIT_SECONDS,
        USER_ACCT_LOGOUT,
    ],
    # call authorize twice (1st call and 2nd call) - only 1st call emit email notification
    "first_api_call_email": [
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        CLICK_AGREE_ACCESS,
        VALIDATE_1ST_APP_CREATED_EMAIL,
        {"sequence": SEQ_AUTHORIZE_RESTART},
        CALL_LOGIN,
        CLICK_AGREE_ACCESS,
        VALIDATE_1ST_APP_CREATED_EMAIL,
    ]
}
