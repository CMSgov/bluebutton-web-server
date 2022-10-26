from django.conf import settings
from enum import Enum
from selenium.webdriver.common.by import By

PROD_URL = 'https://api.bluebutton.cms.gov'

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
    GET_SAMPLE_TOKEN_START = 10
    GET_SAMPLE_TOKEN_PKCE_START = 11
    SLEEP = 12


TESTCLIENT_BUNDLE_LABEL_FMT = "Response (Bundle of {}), API version: {}"
TESTCLIENT_RESOURCE_LABEL_FMT = "Response ({}), API version: {}"
MESSAGE_NO_PERMISSION = "You do not have permission to perform this action."
TESTCASE_BANNER_FMT = "** {} TEST: {}, API: {}, STEP: {}, {}"
'''
UI Widget text: texts on e.g. buttons, links, labels etc.
'''
LNK_TXT_TESTCLIENT = "Test Client"
LNK_TXT_GET_TOKEN_V1 = "Get a Sample Authorization Token"
LNK_TXT_GET_TOKEN_V2 = "Get a Sample Authorization Token for v2"
LNK_TXT_GET_TOKEN_PKCE_V1 = "Get a Sample Authorization Token (PKCE Enabled)"
LNK_TXT_GET_TOKEN_PKCE_V2 = "Get a Sample Authorization Token for v2 (PKCE Enabled)"
LNK_TXT_AUTH_AS_BENE = "Authorize as a Beneficiary"
LNK_TXT_RESTART_TESTCLIENT = "restart testclient"
TAG_FOR_AUTHORIZE_LINK = "pre"
# FHIR search result bundle pagination
LNK_TXT_NAV_FIRST = "first"
LNK_TXT_NAV_NEXT = "next"
LNK_TXT_NAV_PREV = "previous"
LNK_TXT_NAV_LAST = "last"
LNK_TXT_NAV_SELF = "self"
# FHIR resources query page
LNK_TXT_PATIENT = "Patient"
LNK_TXT_EOB = "ExplanationOfBenefit"
LNK_TXT_COVERAGE = "Coverage"
LNK_TXT_PROFILE = "Profile"
LNK_TXT_METADATA = "FHIR Metadata"
LNK_TXT_OIDC_DISCOVERY = "OIDC Discovery"
# FHIR result page label H2
LAB_FHIR_RESULTPAGE_H2 = "h2"
CONTENT_FHIR_RESULTPAGE_PRE = "pre"
# MSLSX login form
TXT_FLD_SUB_MSLSX = "username"
TXT_FLD_HICN_MSLSX = "hicn"
TXT_FLD_MBI_MSLSX = "mbi"
TXT_FLD_VAL_SUB_MSLSX = "fred"
MSLSX_TXT_FLD_HICN_VAL = "1000044680"
MSLSX_TXT_FLD_MBI_VAL = "2SW4N00AA00"
MSLSX_CSS_BUTTON = "button"
# SLSX login form
SLSX_TXT_FLD_USERNAME = "username-textbox"
SLSX_TXT_FLD_PASSWORD = "password-textbox"
SLSX_TXT_FLD_USERNAME_VAL = "BBUser29001"
SLSX_TXT_FLD_PASSWORD_VAL = "PW29001!"
SLSX_CSS_BUTTON = "login-button"
# Demographic info access grant form
BTN_ID_GRANT_DEMO_ACCESS = "approve"
BTN_ID_DENY_DEMO_ACCESS = "deny"
BTN_ID_RADIO_NOT_SHARE = "label:nth-child(5)"
# API versions
API_V2 = "v2"
API_V1 = "v1"

BROWSERBACK = {
    "display": "Back to FHIR resource page",
    "action": Action.BACK,
}

WAIT_SECONDS = {
    "display": "Sleep seconds...",
    "action": Action.SLEEP,
    "params": [3],
}

CHECK_TESTCLIENT_START_PAGE = {
    "display": "Check it's on 'Test Client' start page",
    "action": Action.FIND,
    "params": [30, By.LINK_TEXT, LNK_TXT_GET_TOKEN_V1]
}

CLICK_TESTCLIENT = {
    "display": "Click link 'Test Client'",
    "action": Action.FIND_CLICK,
    "params": [30, By.LINK_TEXT, LNK_TXT_TESTCLIENT]
}

LOAD_TESTCLIENT_HOME = {
    "display": "Load Test Client Home Page",
    "action": Action.LOAD_PAGE,
    "params": [settings.HOSTNAME_URL + "/testclient"]
}

CLICK_RADIO_NOT_SHARE = {
    "display": "Click 'Share healthcare data, but not your personal info' on DEMO info grant form",
    "action": Action.FIND_CLICK,
    "params": [20, By.CSS_SELECTOR, BTN_ID_RADIO_NOT_SHARE]
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

CALL_LOGIN = {
    "display": "Start login ...",
    "action": Action.LOGIN,
}

SEQ_LOGIN_MSLSX = [
    {
        "display": "Input SUB(username)",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, TXT_FLD_SUB_MSLSX, TXT_FLD_VAL_SUB_MSLSX]
    },
    {
        "display": "Input hicn",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, TXT_FLD_HICN_MSLSX, MSLSX_TXT_FLD_HICN_VAL]
    },
    {
        "display": "Input mbi",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.NAME, TXT_FLD_MBI_MSLSX, MSLSX_TXT_FLD_MBI_VAL]
    },
    {
        "display": "Click 'submit' on MSLSX login form",
        "action": Action.FIND_CLICK,
        "params": [20, By.CSS_SELECTOR, MSLSX_CSS_BUTTON]
    },
]

SEQ_LOGIN_SLSX = [
    {
        "display": "Medicare.gov login username",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, SLSX_TXT_FLD_USERNAME, SLSX_TXT_FLD_USERNAME_VAL]
    },
    {
        "display": "Medicare.gov login password",
        "action": Action.FIND_SEND_KEY,
        "params": [20, By.ID, SLSX_TXT_FLD_PASSWORD, SLSX_TXT_FLD_PASSWORD_VAL]
    },
    {
        "display": "Click 'submit' on SLSX login form",
        "action": Action.FIND_CLICK,
        "params": [20, By.ID, SLSX_CSS_BUTTON]
    },
]

SEQ_AUTHORIZE_START = [
    {
        "display": "Load BB2 Landing Page ...",
        "action": Action.LOAD_PAGE,
        "params": [settings.HOSTNAME_URL]
    },
    CLICK_TESTCLIENT if not settings.HOSTNAME_URL.startswith(PROD_URL) else LOAD_TESTCLIENT_HOME,
    {
        "display": "Click link to get sample token v1/v2",
        "action": Action.GET_SAMPLE_TOKEN_START,
    },
    {
        "display": "Click link 'Authorize as a Beneficiary' - start authorization",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, LNK_TXT_AUTH_AS_BENE]
    },
]

SEQ_AUTHORIZE_PKCE_START = [
    {
        "display": "Load BB2 Landing Page ...",
        "action": Action.LOAD_PAGE,
        "params": [settings.HOSTNAME_URL]
    },
    CLICK_TESTCLIENT if not settings.HOSTNAME_URL.startswith(PROD_URL) else LOAD_TESTCLIENT_HOME,
    {
        "display": "Click link to get sample token v1/v2 with PKCE enabled",
        "action": Action.GET_SAMPLE_TOKEN_PKCE_START,
    },
    {
        "display": "Check authorize link for PKCE challenge info present",
        "action": Action.CHECK_PKCE_CHALLENGE,
        "params": [20, By.TAG_NAME, TAG_FOR_AUTHORIZE_LINK, True]
    },
    {
        "display": "Click link 'Authorize as a Beneficiary' - start authorization",
        "action": Action.FIND_CLICK,
        "params": [30, By.LINK_TEXT, LNK_TXT_AUTH_AS_BENE]
    },
]

SEQ_QUERY_FHIR_RESOURCES = [
    {
        "display": "Click 'Patient' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_PATIENT]
    },
    {
        "display": "Check Patient result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_PATIENT]
    },
    BROWSERBACK,
    {
        "display": "Click 'Coverage' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_COVERAGE]
    },
    {
        "display": "Check Coverage result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, LNK_TXT_COVERAGE]
    },
    {
        "display": "Check and click Coverage result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_NAV_LAST]
    },
    CLICK_TESTCLIENT if not settings.HOSTNAME_URL.startswith(PROD_URL) else LOAD_TESTCLIENT_HOME,
    {
        "display": "Click 'ExplanationOfBenefit' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_EOB]
    },
    {
        "display": "Check ExplanationOfBenefit result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, LNK_TXT_EOB]
    },
    {
        "display": "Check and click ExplanationOfBenefit result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_NAV_LAST]
    },
    WAIT_SECONDS,
    CLICK_TESTCLIENT if not settings.HOSTNAME_URL.startswith(PROD_URL) else LOAD_TESTCLIENT_HOME,
    WAIT_SECONDS,
    {
        "display": "Click 'Profile' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_PROFILE]
    },
    WAIT_SECONDS,
    {
        "display": "Check Profile result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT,
                   "{} (OIDC Userinfo)".format(LNK_TXT_PROFILE)]
    },
    BROWSERBACK,
    {
        "display": "Click 'FHIR Metadata' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_METADATA]
    },
    {
        "display": "Check FHIR Metadata result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_METADATA]
    },
    BROWSERBACK,
    {
        "display": "Click 'OIDC Discovery' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_OIDC_DISCOVERY]
    },
    {
        "display": "Check OIDC Discovery result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_OIDC_DISCOVERY]
    },
    BROWSERBACK,
]

SEQ_QUERY_FHIR_RESOURCES_NO_DEMO = [
    {
        "display": "Click 'Patient' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_PATIENT]
    },
    {
        "display": "Check Patient result page content (<pre>) expect no permission message",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.TAG_NAME, CONTENT_FHIR_RESULTPAGE_PRE, MESSAGE_NO_PERMISSION]
    },
    BROWSERBACK,
    {
        "display": "Click 'Coverage' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_COVERAGE]
    },
    {
        "display": "Check Coverage result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, LNK_TXT_COVERAGE]
    },
    {
        "display": "Check and click Coverage result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_NAV_LAST]
    },
    CLICK_TESTCLIENT if not settings.HOSTNAME_URL.startswith(PROD_URL) else LOAD_TESTCLIENT_HOME,
    {
        "display": "Click 'ExplanationOfBenefit' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_EOB]
    },
    {
        "display": "Check ExplanationOfBenefit result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_BUNDLE_LABEL_FMT, LNK_TXT_EOB]
    },
    {
        "display": "Check and click ExplanationOfBenefit result page navigation links 'last'",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_NAV_LAST]
    },
    WAIT_SECONDS,
    CLICK_TESTCLIENT if not settings.HOSTNAME_URL.startswith(PROD_URL) else LOAD_TESTCLIENT_HOME,
    WAIT_SECONDS,
    {
        "display": "Click 'Profile' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_PROFILE]
    },
    WAIT_SECONDS,
    {
        "display": "Check Profile result page content (<pre>) expect no permission message",
        "action": Action.CONTAIN_TEXT,
        "params": [20, By.TAG_NAME, CONTENT_FHIR_RESULTPAGE_PRE, MESSAGE_NO_PERMISSION]
    },
    BROWSERBACK,
    {
        "display": "Click 'FHIR Metadata' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_METADATA]
    },
    {
        "display": "Check FHIR Metadata result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_METADATA]
    },
    BROWSERBACK,
    {
        "display": "Click 'OIDC Discovery' on FHIR resources page",
        "action": Action.FIND_CLICK,
        "params": [20, By.LINK_TEXT, LNK_TXT_OIDC_DISCOVERY]
    },
    {
        "display": "Check OIDC Discovery result page title",
        "action": Action.CHECK,
        "params": [20, By.TAG_NAME, LAB_FHIR_RESULTPAGE_H2, TESTCLIENT_RESOURCE_LABEL_FMT, LNK_TXT_OIDC_DISCOVERY]
    },
    BROWSERBACK,
]

TESTS = {
    "auth_grant_fhir_calls": [
        {"sequence": SEQ_AUTHORIZE_START},
        CALL_LOGIN,
        CLICK_AGREE_ACCESS,
        {"sequence": SEQ_QUERY_FHIR_RESOURCES}
    ],
    "auth_grant_pkce_fhir_calls": [
        {"sequence": SEQ_AUTHORIZE_PKCE_START},
        CALL_LOGIN,
        CLICK_AGREE_ACCESS,
        {"sequence": SEQ_QUERY_FHIR_RESOURCES}
    ],
    "auth_deny_fhir_calls": [
        {"sequence": SEQ_AUTHORIZE_START},
        CALL_LOGIN,
        CLICK_DENY_ACCESS,
        CHECK_TESTCLIENT_START_PAGE
    ],
    "auth_grant_w_no_demo": [
        {"sequence": SEQ_AUTHORIZE_START},
        CALL_LOGIN,
        CLICK_RADIO_NOT_SHARE,
        CLICK_AGREE_ACCESS,
        {"sequence": SEQ_QUERY_FHIR_RESOURCES_NO_DEMO}
    ]
}
