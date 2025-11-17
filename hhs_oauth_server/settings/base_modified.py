import os
from apps.logging.sensitive_logging_filters import SENSITIVE_DATA_FILTER, SensitiveDataFilter
import dj_database_url
import socket
import datetime
from getenv import env
from ..utils import bool_env, int_env
from urllib.parse import urlparse

from django.contrib.messages import constants as messages
from django.utils.translation import gettext_lazy as _
from .themes import THEMES, THEME_SELECTED


# ############################################################################
# ############################################################################
# DJANGO CORE SETTINGS
# ############################################################################
# ############################################################################

# ============================================================================
# Application Configuration
# ============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(BASE_DIR, "..")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, ("templates/"))],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django_settings_export.settings_export",
                "hhs_oauth_server.hhs_oauth_server_context.active_apps",
            ],
            "builtins": [],
        },
    },
]

# ============================================================================
# Security & Keys
# ============================================================================

SECRET_KEY = env(
    "DJANGO_SECRET_KEY", "FAKE_SECRET_KEY_YOU_MUST_SET_DJANGO_SECRET_KEY_VAR"
)
if SECRET_KEY == "FAKE_SECRET_KEY_YOU_MUST_SET_DJANGO_SECRET_KEY_VAR":
    print(
        "WARNING: Generate your secret key and set in environment "
        "variable: DJANGO_SECRET_KEY"
    )

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", ["*", socket.gethostname()])
DEBUG = env("DEBUG", False)

# ============================================================================
# Installed Apps / Middleware
# ============================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "rest_framework",
    "rest_framework_csv",
    "django_filters",
    # 1st Party (in-house) ----------
    "apps.accounts",
    "apps.capabilities",
    "apps.core",
    "apps.wellknown",
    "apps.health",
    "apps.docs",
    # Use AppConfig to set apps.dot_ext to dot_ext so that splits in
    # django.db.models.utils doesn't have more than 2 values
    # There probably should be an edit to django.db so that the split
    # could deal with apps.dot_ext.model_name when it encounters a string
    # TODO I don't think this is needed, apps register as the last item (after the last .)
    "apps.dot_ext.apps.dot_extConfig",
    "apps.pkce",
    "apps.home",
    "apps.fhir.server",
    "apps.fhir.bluebutton",
    "apps.mymedicare_cb",
    "apps.authorization",
    "apps.bb2_tools",
    # 3rd Party ---------------------
    "corsheaders",
    "bootstrap5",
    "waffle",
    # DOT must be installed after apps.dot_ext in order to override templates
    "oauth2_provider",
    "axes",
    "apps.logging",
    "apps.creds",
]

DEV_SPECIFIC_APPS = [
    # Installation/Site Specific apps based on  -----------------
    # 'storages',
    # A test client - moved to aws-test / dev /impl settings
    "apps.testclient",
]

INSTALLED_APPS += DEV_SPECIFIC_APPS

if env("ENV_SPECIFIC_APPS", False):
    INSTALLED_APPS += env("ENV_SPECIFIC_APPS")

OPTIONAL_INSTALLED_APPS = [
    "",
]

if env("OPTIONAL_INSTALLED_APPS", False):
    OPTIONAL_INSTALLED_APPS += env("OPTIONAL_INSTALLED_APPS")

MIDDLEWARE = [
    # Middleware that adds headers to the resposne
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "hhs_oauth_server.request_logging.RequestTimeLoggingMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    # Must be before CommonMiddleware but after SessionMiddleware
    "django.middleware.locale.LocaleMiddleware",
    # Middleware that can send a response must be below this line
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.dot_ext.throttling.ThrottleMiddleware",
    "waffle.middleware.WaffleMiddleware",
    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    # It only formats user lockout messages and renders Axes lockout responses
    # on failed user authentication attempts from login views.
    # If you do not want Axes to override the authentication response
    # you can skip installing the middleware and use your own views.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "hhs_oauth_server.urls"

# ============================================================================
# Static / Media Files
# ============================================================================

WSGI_APPLICATION = "hhs_oauth_server.wsgi.application"

ASSETS_ROOT = env("DJANGO_ASSETS_ROOT", BASE_DIR)
MEDIA_ROOT = os.path.join(ASSETS_ROOT, "media")
MEDIA_URL = "/media/"
STATIC_URL = "/static/"
STATIC_ROOT = "collectedstatic"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "bluebutton-css"),
    os.path.join(BASE_DIR, "static"),
]

# ============================================================================
# Database / Caching
# ============================================================================

DATABASES = {
    "default": dj_database_url.config(
        default=env("DATABASES_CUSTOM", "sqlite:///{}/db.sqlite3".format(BASE_DIR))
    ),
}

CACHES = {
    "default": {
        "BACKEND": os.environ.get(
            "CACHE_BACKEND", "django.core.cache.backends.db.DatabaseCache"
        ),
        "LOCATION": os.environ.get("CACHE_LOCATION", "django_cache"),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# ============================================================================
# Internationalization / Localization
# ============================================================================

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, ("templates/design_system/locale")),
]

ENCODING = "utf-8"

# ============================================================================
# Email Configuration
# ============================================================================

DEFAULT_FROM_EMAIL = env("DJANGO_FROM_EMAIL", "change-me@example.com")
DEFAULT_ADMIN_EMAIL = env("DJANGO_ADMIN_EMAIL", "change-me@example.com")
# TODO - Verify usage, found in deployment repo, but not used by Django and it seems like
# we only set it, never use it

EMAIL_BACKEND_DEFAULT = "django.core.mail.backends.console.EmailBackend"
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", EMAIL_BACKEND_DEFAULT)
EMAIL_HOST = env("DJANGO_EMAIL_HOST", "email-smtp.us-east-1.amazonaws.com")
EMAIL_PORT = int_env(env("DJANGO_EMAIL_PORT", 587))
EMAIL_USE_TLS = bool_env(env("DJANGO_EMAIL_USE_TLS", "True"))
EMAIL_USE_SSL = bool_env(env("DJANGO_EMAIL_USE_SSL", "False"))
EMAIL_TIMEOUT = env("DJANGO_EMAIL_TIMEOUT", None)
EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD", None)
EMAIL_SSL_KEYFILE = env("DJANGO_EMAIL_SSL_KEYFILE", None)
EMAIL_SSL_CERTFILE = env("DJANGO_EMAIL_SSL_CERTFILE", None)

# ============================================================================
# Logging
# ============================================================================

LOG_JSON_FORMAT_PRETTY = env("DJANGO_LOG_JSON_FORMAT_PRETTY", False)

LOGGING = env(
    "DJANGO_LOGGING",
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(asctime)s %(levelname)s "
                "[%(process)d] %(name)s line:%(lineno)d %(message)s"
            },
            "simple": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
            "jsonout": {
                "format": '{"env": "'
                + env("TARGET_ENV", "DEV")
                + '", "time": "%(asctime)s", "level": "%(levelname)s", '
                '"name": "%(name)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
                "filters": [SENSITIVE_DATA_FILTER],
            }
        },
        "filters": {
            "sensitive_data_filter": {
                "()": SensitiveDataFilter,
            }
        },
        "loggers": {
            "hhs_server": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
            "hhs_oauth_server.accounts": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
            "oauth2_provider": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "oauthlib": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "unsuccessful_logins": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "admin_interface": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "tests": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
            "audit": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "performance": {
                "handlers": ["console"],
                "level": "INFO",
            },
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
            },
        },
    },
)

MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# ============================================================================
# Authentication / Sessions / Login
# ============================================================================

AUTH_PROFILE_MODULE = "accounts.UserProfile"
# TODO - Verify usage, unable to find in code search, deprecated I think

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation." "MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation." "CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation." "NumericPasswordValidator",
    },
    {
        "NAME": "apps.accounts.validators." "PasswordReuseAndMinAgeValidator",
        "OPTIONS": {
            # password minimum age in seconds (5 min)
            "password_min_age": 60 * 5,
            # password reuse interval in seconds (365 days)
            "password_reuse_interval": 60 * 60 * 24 * 365,
            "password_expire": 0,
        },
    },
    {
        "NAME": "apps.accounts.validators." "PasswordComplexityValidator",
        "OPTIONS": {
            "min_length_digit": 1,
            "min_length_alpha": 1,
            "min_length_special": 1,
            "min_length_lower": 1,
            "min_length_upper": 1,
            "special_characters": "[~!{}@#$%^&*_+\":;()'[]",
        },
    },
]

PASSWORD_HASH_ITERATIONS = int(env("DJANGO_PASSWORD_HASH_ITERATIONS", "200000"))

PASSWORD_RULES = [
    {
        "name": "min_length_digit",
        "regex": "[0-9]",
        "msg": "Password must contain at least {} digit(s).",
        "help": "{} digit(s)",
        "min_len": 1,
    },
    {
        "name": "min_length_alpha",
        "regex": "[a-zA-Z]",
        "msg": "Password must contain at least {} letter(s).",
        "help": "{} letter(s)",
        "min_len": 1,
    },
    {
        "name": "min_length_special",
        "regex": "[~!{}@#$%^&*_+\":;()'[]",
        "msg": "Password must contain at least {} special character(s).",
        "help": "{} special char(s)",
        "min_len": 1,
    },
    {
        "name": "min_length_lower",
        "regex": "[a-z]",
        "msg": "Password must contain at least {} lower case letter(s)",
        "help": "{} lower case char(s)",
        "min_len": 1,
    },
    {
        "name": "min_length_upper",
        "regex": "[A-Z]",
        "msg": "Password must contain at least {} upper case letter(s).",
        "help": "{} upper case char(s)",
        "min_len": 1,
    },
]

AUTHENTICATION_BACKENDS = (
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesBackend",
    "apps.accounts.backends.EmailAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
)

SESSION_COOKIE_AGE = 5400
SESSION_COOKIE_SECURE = env("DJANGO_SECURE_SESSION", True)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/v1/accounts/login"
LOGOUT_REDIRECT_URL = "/"

ADMIN_PREPEND_URL = env("DJANGO_ADMIN_PREPEND_URL", "")

# ############################################################################
# ############################################################################
# PYTHON PACKAGE SETTINGS
# ############################################################################
# ############################################################################

# ============================================================================
# django-rest-framework
# ============================================================================

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "token": env("TOKEN_THROTTLE_RATE", "100000/s"),
    },
}

# ============================================================================
# django-axes
# ============================================================================

AXES_COOLOFF_TIME = datetime.timedelta(minutes=30)
AXES_FAILURE_LIMIT = 5
AXES_LOGIN_FAILURE_LIMIT = 5
AXES_LOCK_OUT_AT_FAILURE = True
AXES_ONLY_USER_FAILURES = True
AXES_USERNAME_FORM_FIELD = "username"

# ============================================================================
# django-cors-headers
# ============================================================================

CORS_ORIGIN_ALLOW_ALL = bool_env(env("CORS_ORIGIN_ALLOW_ALL", True))

# ============================================================================
# django-waffle
# ============================================================================

WAFFLE_FLAG_MODEL = "core.Flag"

# ============================================================================
# django-oauth-toolkit
# ============================================================================

OAUTH2_PROVIDER_APPLICATION_MODEL = "dot_ext.Application"
OAUTH2_PROVIDER = {
    "PKCE_REQUIRED": False,
    "OAUTH2_VALIDATOR_CLASS": "apps.dot_ext.oauth2_validators."
    "SingleAccessTokenValidator",
    "OAUTH2_SERVER_CLASS": "apps.dot_ext.oauth2_server.Server",
    "SCOPES_BACKEND_CLASS": "apps.dot_ext.scopes.CapabilitiesScopes",
    "OAUTH2_BACKEND_CLASS": "apps.dot_ext.oauth2_backends.OAuthLibSMARTonFHIR",
    "ALLOWED_REDIRECT_URI_SCHEMES": ["https", "http"],
    "CLIENT_ID_GENERATOR_CLASS": "oauth2_provider.generators.ClientIdGenerator",
    "CLIENT_SECRET_GENERATOR_CLASS": "oauth2_provider.generators.ClientSecretGenerator",
}

DOT_EXPIRES_IN = (
    (86400 * 365 * 5, _("5 Years")),
    (86400, _("1 Day")),
    (86400 * 7, _("1 Week")),
    (86400 * 365, _("1 Year")),
    (86400 * 365 * 3, _("3 Years")),
    (86400 * 365 * 10, _("10 Years")),
    (86400 * 365 * 100, _("Forever")),
)

GRANT_AUTHORIZATION_CODE = "authorization-code"
GRANT_IMPLICIT = "implicit"
GRANT_TYPES = (
    (GRANT_AUTHORIZATION_CODE, _("Authorization code")),
    (GRANT_IMPLICIT, _("Implicit")),
)


# ############################################################################
# ############################################################################
# BLUE BUTTON SETTINGS
# ############################################################################
# ############################################################################

# ============================================================================
# UI Configuration
# ============================================================================

THEME = THEMES[THEME_SELECTED]

APP_LOGO_SIZE_MAX = env("DJANGO_APP_LOGO_SIZE_MAX", "100")
APP_LOGO_WIDTH_MAX = env("DJANGO_APP_LOGO_WIDTH_MAX", "128")
APP_LOGO_HEIGHT_MAX = env("DJANGO_APP_LOGO_HEIGHT_MAX", "128")

APPLICATION_TITLE = env("DJANGO_APPLICATION_TITLE", "Blue Button 2.0")
ORGANIZATION_TITLE = env(
    "DJANGO_ORGANIZATION_TITLE",
    "The U.S. Centers for Medicare & Medicaid Services (CMS)",
)
ORGANIZATION_URI = os.environ.get("DJANGO_ORGANIZATION_URI", "https://cms.gov")
ORGANIZATION_NAME = "CMS Medicare Blue Button"

POLICY_URI = os.environ.get(
    "DJANGO_POLICY_URI",
    "https://www.cms.gov/About-CMS/Agency-Information/Aboutwebsite/Privacy-Policy.html",
)
POLICY_TITLE = env("DJANGO_POLICY_TITLE", "Privacy Policy")

TOS_URI = env("DJANGO_TOS_URI", "https://bluebutton.cms.gov/terms")
TOS_TITLE = env("DJANGO_TOS_TITLE", "Terms of Service")

TAG_LINE_1 = env("DJANGO_TAG_LINE_1", "Share your Medicare data")
TAG_LINE_2 = env(
    "DJANGO_TAG_LINE_2", "with applications, organizations, and people you trust."
)
EXPLAINATION_LINE = "This service allows Medicare beneficiaries to connect their health data to applications of their choosing."
EXPLAINATION_LINE = env("DJANGO_EXPLAINATION_LINE ", EXPLAINATION_LINE)

EXTERNAL_AUTH_NAME = "Medicare.gov"
ALLOW_END_USER_EXTERNAL_AUTH = "B"

DEVELOPER_DOCS_URI = "https://bluebutton.cms.gov/developers"
DEVELOPER_DOCS_TITLE = "Documentation"

DEFAULT_DISCLOSURE_TEXT = """
    This system is provided for use by 3rd party application developers
    to register a beneficiary-facing application.  See the documentation
    for more information on proper use. Unauthorized or improper use of this
    system or its data may result in disciplinary action, as well as civil
    and criminal penalties. This system may be monitored, recorded and
    subject to audit.
    """

DISCLOSURE_TEXT = env("DJANGO_PRIVACY_POLICY_URI", DEFAULT_DISCLOSURE_TEXT)

# ============================================================================
# Application Config
# ============================================================================

APP_LIST_EXCLUDE = env("DJANGO_APP_LIST_EXCLUDE", ["internal-use"])

BLOCK_HTTP_REDIRECT_URIS = False
IS_MEDIA_URL_LOCAL = False

CREDENTIALS_REQUEST_URL_TTL = 5
SIGNUP_TIMEOUT_DAYS = env("SIGNUP_TIMEOUT_DAYS", 7)

OFFLINE = False
# TODO - Verify usage, unable to find in code search

EXTERNAL_LOGIN_TEMPLATE_NAME = "/v1/accounts/upstream-login"
# TODO - Verify usage, unable to find in code search

# ============================================================================
# FHIR Config
# ============================================================================

FHIR_CLIENT_CERTSTORE = env(
    "DJANGO_FHIR_CERTSTORE",
    os.path.join(BASE_DIR, os.environ.get("DJANGO_FHIR_CERTSTORE_REL", "../certstore")),
)

FHIR_SERVER = {
    # Strip trailing '/' from all URLs. We expect hostnames/paths to *not* have a trailing slash
    # throughout the codebase. Allowing a '/' through at the end here will create many situations where
    # URLs have a "//" embedded within them, and may cause problems for tests and other substring matches.
    "FHIR_URL": env("FHIR_URL", "https://invalid_fhir_url.gov").rstrip("/"),
    "FHIR_URL_V3": env("FHIR_URL_V3", "https://invalid_fhir_url_v3.gov").rstrip("/"),
    "CERT_FILE": os.path.join(
        FHIR_CLIENT_CERTSTORE, env("FHIR_CERT_FILE", "ca.cert.pem")
    ),
    "KEY_FILE": os.path.join(
        FHIR_CLIENT_CERTSTORE, env("FHIR_KEY_FILE", "ca.key.nocrypt.pem")
    ),
    "CLIENT_AUTH": True,
}

MOCK_FHIR_ENDPOINT_HOSTNAME = urlparse(FHIR_SERVER["FHIR_URL"]).hostname

FHIR_POST_SEARCH_PARAM_IDENTIFIER_MBI_HASH = (
    "https://bluebutton.cms.gov/resources/identifier/mbi-hash"
)
# TODO - Move to constants

FHIR_POST_SEARCH_PARAM_IDENTIFIER_HICN_HASH = (
    "https://bluebutton.cms.gov/resources/identifier/hicn-hash"
)
# TODO - Move to constants

FHIR_PATIENT_SEARCH_PARAM_IDENTIFIER_MBI = (
    "http://hl7.org/fhir/sid/us-mbi"
)
# TODO - Move to constants

FHIR_PARAM_FORMAT = "json"

BENE_PERSONAL_INFO_SCOPES = [
    "patient/Patient.read",
    "patient/Patient.s",
    "patient/Patient.r",
    "patient/Patient.rs",
    "profile",
]

# ============================================================================
# Request Configuration
# ============================================================================

HOSTNAME_URL = env("HOSTNAME_URL", "http://localhost:8000")

REQUEST_CALL_TIMEOUT = (30, 120)
# TODO - Verify usage, unable to find in code search

REQUEST_EOB_KEEP_ALIVE = "timeout=120, max=10"

TESTCLIENT_REDIRECT_URI = "/testclient/callback"

# ============================================================================
# User Identification
# ============================================================================

USER_ID_SALT = env("DJANGO_USER_ID_SALT", "6E6F747468657265616C706570706572")

# Check type for cases where this is an INT in local development
iterations = env("DJANGO_USER_ID_ITERATIONS", None)
if iterations:
    if isinstance(iterations, int):
        USER_ID_ITERATIONS = iterations
    elif isinstance(iterations, str):
        USER_ID_ITERATIONS = int(iterations)
else:
    # Default for local development when ENV not set
    USER_ID_ITERATIONS = 2

USER_ID_TYPE_CHOICES = (("H", "HICN"), ("M", "MBI"))

USER_ID_TYPE_DEFAULT = "H"
DEFAULT_SAMPLE_FHIR_ID_V2 = env("DJANGO_DEFAULT_SAMPLE_FHIR_ID_V2", "-20140000008325")
DEFAULT_SAMPLE_FHIR_ID_V3 = env("DJANGO_DEFAULT_SAMPLE_FHIR_ID_V3", "-30250000008325")

# ============================================================================
# Medicare / SLSx Authentication
# ============================================================================

SLSX_CLIENT_ID = env("DJANGO_SLSX_CLIENT_ID")
SLSX_CLIENT_SECRET = env("DJANGO_SLSX_CLIENT_SECRET")

MEDICARE_SLSX_AKAMAI_ACA_TOKEN = env("DJANGO_MEDICARE_SLSX_AKAMAI_ACA_TOKEN", "")

MEDICARE_SLSX_REDIRECT_URI = env(
    "DJANGO_MEDICARE_SLSX_REDIRECT_URI", "http://localhost:8000/mymedicare/sls-callback"
)

MEDICARE_SLSX_LOGIN_URI = env(
    "DJANGO_MEDICARE_SLSX_LOGIN_URI",
    "https://test.medicare.gov/sso/authorize?client_id=bb2api",
)

SLSX_TOKEN_ENDPOINT = env(
    "DJANGO_SLSX_TOKEN_ENDPOINT", "https://test.medicare.gov/sso/session"
)

SLSX_USERINFO_ENDPOINT = env(
    "DJANGO_SLSX_USERINFO_ENDPOINT", "https://test.accounts.cms.gov/v1/users"
)

SLSX_HEALTH_CHECK_ENDPOINT = env(
    "DJANGO_SLSX_HEALTH_CHECK_ENDPOINT", "https://test.accounts.cms.gov/health"
)

SLSX_SIGNOUT_ENDPOINT = env(
    "DJANGO_SLSX_SIGNOUT_ENDPOINT", "https://test.medicare.gov/sso/signout"
)

SLSX_VERIFY_SSL_INTERNAL = env("DJANGO_SLSX_VERIFY_SSL_INTERNAL", False)
SLSX_VERIFY_SSL_EXTERNAL = env("DJANGO_SLSX_VERIFY_SSL_EXTERNAL", False)


# ============================================================================
# Error / Status Messages
# TODO - These should be moved to __init__.py or a constants.py file
# ============================================================================

MEDICARE_ERROR_MSG = "An error occurred connecting to medicare.gov account"

APPLICATION_TEMPORARILY_INACTIVE = (
    'This application, {}, is temporarily inactive.'
    ' If you are the app maintainer, please contact the Blue Button API team.'
    ' If you are a Medicare Beneficiary and need assistance, please contact'
    ' the support team for the application you are trying to access.'
)

APPLICATION_RESEARCH_STUDY_ENDED_MESG = (
    "Application end date passed. "
    "Contact us at BlueButtonAPI@cms.hhs.gov if you need to refresh Medicare data."
)

APPLICATION_ONE_TIME_REFRESH_NOT_ALLOWED_MESG = (
    'Your application is not allowed to refresh tokens. '
    'To refresh Medicare data, end user must re-authenticate '
    'and consent to share their data. '
    'If your application needs to refresh tokens, contact us at BlueButtonAPI@cms.hhs.gov.'
)

APPLICATION_NOT_AUTHENTICATED = (
    'Application not authenticated. '
    'To refresh Medicare data, end user must re-authenticate '
    'and consent to share their data.'
)

APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_EXPIRED_MESG = (
    'User access has timed out. '
    'To refresh Medicare data, end user must re-authenticate '
    'and consent to share their data.'
)

APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_NOT_FOUND_MESG = (
    'User access cannot be found. '
    'To refresh Medicare data, end user must re-authenticate '
    'and consent to share their data.'
)

# ============================================================================
# Splunk Dashboard Config
# TODO - Investigate if these still work
# ============================================================================

CMS_SPLUNK_URL = env("CMS_SPLUNK_URL", "https://splunk.cloud.cms.gov")

SPLUNK_DASHBOARDS = [
    {
        "display_name": "BB2 Authorization Flow Dashboard",
        "url": "{}/en-US/app/cms_bbapi_landing_app/bb2_authorization_flow_dashboard".format(
            CMS_SPLUNK_URL
        ),
    },
    {
        "display_name": "API Big Stats Dashboard - Structured",
        "url": "{}/en-US/app/cms_bbapi_landing_app/00_api_big_stats_dashboard__structured".format(
            CMS_SPLUNK_URL
        ),
    },
    {
        "display_name": "BB2 DASG Metrics Dashboard",
        "url": "{}/en-US/app/cms_bbapi_landing_app/BB2_DASG_Metrics_Dashboard".format(
            CMS_SPLUNK_URL
        ),
    },
    {
        "display_name": "BB2 V2 Activities Dashboard",
        "url": "{}/en-US/app/cms_bbapi_landing_app/bb2_v2_activities_dashboard".format(
            CMS_SPLUNK_URL
        ),
    },
]

# ============================================================================
# AWS Static & Media File Storage
# ============================================================================

if env("TARGET_ENV", "") in ["dev", "test", "impl", "prod"]:
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN")
    STATICFILES_LOCATION = "static/"
    STATIC_URL = "https://%s%s" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    MEDIAFILES_LOCATION = "media/"
    STORAGES = {
        "default": {
            "BACKEND": "hhs_oauth_server.s3_storage.MediaStorage",
        },
        "staticfiles": {
            "BACKEND": "hhs_oauth_server.s3_storage.StaticStorage",
        },
    }
    MEDIA_URL = "https://%s/%s" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
    # Unsure what this does at the moment
    SEND_EMAIL = True
    CSRF_COOKIE_SECURE = True
else:
    # Setup S3 media storage only for local docker testing.
    # NOTE: To test, place variables in the .env file of the project root directory.
    #
    #     The following ENV variables are needed:
    #         AWS_STORAGE_BUCKET_NAME, AWS_S3_CUSTOM_DOMAIN
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN")
    if AWS_S3_CUSTOM_DOMAIN:
        AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
        MEDIAFILES_LOCATION = "media/"
        STATICFILES_LOCATION = "static/"
        DEFAULT_FILE_STORAGE = "hhs_oauth_server.s3_storage.MediaStorage"
        MEDIA_URL = "https://%s/%s" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
    else:
        # This sets up a media path in urls.py when set for local storage.
        IS_MEDIA_URL_LOCAL = True
