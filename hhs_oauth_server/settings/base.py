import os
from apps.logging.sensitive_logging_filters import SENSITIVE_DATA_FILTER, SensitiveDataFilter
import dj_database_url
import socket
import datetime
from getenv import env
from ..utils import bool_env, int_env

from django.contrib.messages import constants as messages
from django.utils.translation import gettext_lazy as _
from .themes import THEMES, THEME_SELECTED


# project root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(BASE_DIR, "..")

# security
SECRET_KEY = env(
    "DJANGO_SECRET_KEY", "FAKE_SECRET_KEY_YOU_MUST_SET_DJANGO_SECRET_KEY_VAR"
)
if SECRET_KEY == "FAKE_SECRET_KEY_YOU_MUST_SET_DJANGO_SECRET_KEY_VAR":
    print(
        "WARNING: Generate your secret key and set in environment "
        "variable: DJANGO_SECRET_KEY"
    )

CMS_SPLUNK_URL = env("CMS_SPLUNK_URL", "https://splunk.cloud.cms.gov")

# splunk dashboards links:
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

# password rules used by validator: PasswordComplexityValidator,
# this is part of the validation logic, exercise caution when make changes
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

PASSWORD_HASH_ITERATIONS = int(env("DJANGO_PASSWORD_HASH_ITERATIONS", "200000"))

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", ["*", socket.gethostname()])

DEBUG = env("DEBUG", False)

# apps and middlewares
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

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "token": env("TOKEN_THROTTLE_RATE", "100000/s"),
        # "token": os.environ.get("TOKEN_THROTTLE_RATE", "100000/s"),
    },
}

# Failed Login Attempt Module: AXES
# Either integer or timedelta.
# If integer interpreted, as hours
AXES_COOLOFF_TIME = datetime.timedelta(minutes=30)
AXES_FAILURE_LIMIT = 5
AXES_LOGIN_FAILURE_LIMIT = 5
AXES_LOCK_OUT_AT_FAILURE = True
AXES_ONLY_USER_FAILURES = True
AXES_USERNAME_FORM_FIELD = "username"

# Used for testing for optional apps in templates without causing a crash
# used in SETTINGS_EXPORT below.
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

CORS_ORIGIN_ALLOW_ALL = bool_env(env("CORS_ORIGIN_ALLOW_ALL", True))

ROOT_URLCONF = "hhs_oauth_server.urls"

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

WSGI_APPLICATION = "hhs_oauth_server.wsgi.application"

CACHES = {
    "default": {
        "BACKEND": os.environ.get(
            "CACHE_BACKEND", "django.core.cache.backends.db.DatabaseCache"
        ),
        "LOCATION": os.environ.get("CACHE_LOCATION", "django_cache"),
    },
}

# keep backward compatible with AutoField instead of BigAutoField
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

DATABASES = {
    "default": dj_database_url.config(
        default=env("DATABASES_CUSTOM", "sqlite:///{}/db.sqlite3".format(BASE_DIR))
    ),
}

# this helps Django messages format nicely with Bootstrap3
MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# Set the list of supported languages
LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    # Add more languages as needed
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, ("templates/design_system/locale")),
]

# internationalization
LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# static files and media
ASSETS_ROOT = env("DJANGO_ASSETS_ROOT", BASE_DIR)

MEDIA_ROOT = os.path.join(ASSETS_ROOT, "media")

MEDIA_URL = "/media/"
STATIC_URL = "/static/"
STATIC_ROOT = "collectedstatic"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "sitestatic"),
    os.path.join(BASE_DIR, "bluebutton-css"),
    os.path.join(BASE_DIR, "static"),
]

# Waffle
WAFFLE_FLAG_MODEL = "core.Flag"

# emails
DEFAULT_FROM_EMAIL = env("DJANGO_FROM_EMAIL", "change-me@example.com")
DEFAULT_ADMIN_EMAIL = env("DJANGO_ADMIN_EMAIL", "change-me@example.com")

# The console.EmailBackend backend prints to the console.
# Redefine this for SES or other email delivery mechanism
EMAIL_BACKEND_DEFAULT = "django.core.mail.backends.console.EmailBackend"
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", EMAIL_BACKEND_DEFAULT)
EMAIL_HOST = env("DJANGO_EMAIL_HOST", "email-smtp.us-east-1.amazonaws.com")
# SES PORT options: 25, 465, 587, 2465 or 2587.
# Port 25 is throttled
# Use port 587 or 2587 for TLS connections
# Use port 465 or 2465 for Native SSL support
EMAIL_PORT = int_env(env("DJANGO_EMAIL_PORT", 587))
EMAIL_USE_TLS = bool_env(env("DJANGO_EMAIL_USE_TLS", "True"))
EMAIL_USE_SSL = bool_env(env("DJANGO_EMAIL_USE_SSL", "False"))
EMAIL_TIMEOUT = env("DJANGO_EMAIL_TIMEOUT", None)
EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD", None)
EMAIL_SSL_KEYFILE = env("DJANGO_EMAIL_SSL_KEYFILE", None)
EMAIL_SSL_CERTFILE = env("DJANGO_EMAIL_SSL_CERTFILE", None)

# Use env-specific logging config if present
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
            # handy for sql trouble shooting
            # 'django.db.backends': {
            #     'level': 'DEBUG',
            #     'handlers': ['console'],
            # },
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

# Option for local development to pretty print/format JSON logging
LOG_JSON_FORMAT_PRETTY = env("DJANGO_LOG_JSON_FORMAT_PRETTY", False)

AUTH_PROFILE_MODULE = "accounts.UserProfile"

# Django Oauth Tookit settings and customizations
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

# These choices will be available in the expires_in field
# of the oauth2 authorization page.
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

# List of beneficiary personal information resource type scopes
BENE_PERSONAL_INFO_SCOPES = [
    "patient/Patient.read",
    "patient/Patient.s",
    "patient/Patient.r",
    "patient/Patient.rs",
    "profile",
]

# Set the theme
THEME = THEMES[THEME_SELECTED]


APPLICATION_TITLE = env("DJANGO_APPLICATION_TITLE", "Blue Button 2.0")
ORGANIZATION_TITLE = env(
    "DJANGO_ORGANIZATION_TITLE",
    "The U.S. Centers for Medicare & Medicaid Services (CMS)",
)
ORGANIZATION_URI = os.environ.get("DJANGO_ORGANIZATION_URI", "https://cms.gov")
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

# Application model settings
APP_LOGO_SIZE_MAX = env("DJANGO_APP_LOGO_SIZE_MAX", "100")
APP_LOGO_WIDTH_MAX = env("DJANGO_APP_LOGO_WIDTH_MAX", "128")
APP_LOGO_HEIGHT_MAX = env("DJANGO_APP_LOGO_HEIGHT_MAX", "128")

# Application label slugs to exclude from externally
# published lists, like those used for internal use testing.
APP_LIST_EXCLUDE = env("DJANGO_APP_LIST_EXCLUDE", ["internal-use"])

# LINKS TO DOCS
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

HOSTNAME_URL = env("HOSTNAME_URL", "http://localhost:8000")

# Set the default Encoding standard. typically 'utf-8'
ENCODING = "utf-8"

# include settings values in SETTING_EXPORT to use values in Templates.
# eg. {{ settings.APPLICATION_TITLE }}
SETTINGS_EXPORT = [
    "DEBUG",
    "ALLOWED_HOSTS",
    "APPLICATION_TITLE",
    "THEME",
    "STATIC_URL",
    "STATIC_ROOT",
    "MEDIA_URL",
    "MEDIA_ROOT",
    "DEVELOPER_DOCS_URI",
    "DEVELOPER_DOCS_TITLE",
    "ORGANIZATION_TITLE",
    "POLICY_URI",
    "POLICY_TITLE",
    "DISCLOSURE_TEXT",
    "TOS_URI",
    "TOS_TITLE",
    "TAG_LINE_1",
    "TAG_LINE_2",
    "EXPLAINATION_LINE",
    "EXTERNAL_AUTH_NAME",
    "ALLOW_END_USER_EXTERNAL_AUTH",
    "OPTIONAL_INSTALLED_APPS",
    "INSTALLED_APPS",
    "LANGUAGE_COOKIE_NAME"
]

SESSION_COOKIE_AGE = 5400
SESSION_COOKIE_SECURE = env("DJANGO_SECURE_SESSION", True)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

APPLICATION_NOT_FOUND = (
    "No application was found."
)

APPLICATION_TEMPORARILY_INACTIVE = (
    "This application, {}, is temporarily inactive."
    " If you are the app maintainer, please contact the Blue Button 2.0 API team."
    " If you are a Medicare Beneficiary and need assistance,"
    " please contact the application's support team or call 1-800-MEDICARE (1-800-633-4227)"
)

APPLICATION_RESEARCH_STUDY_ENDED_MESG = (
    "Application end date passed. "
    "Contact us at BlueButtonAPI@cms.hhs.gov if you need to refresh Medicare data."
)

APPLICATION_ONE_TIME_REFRESH_NOT_ALLOWED_MESG = (
    "Your application is not allowed to refresh tokens. "
    "To refresh Medicare data, end user must re-authenticate "
    "and consent to share their data."
    "If your application needs to refresh tokens, contact us at BlueButtonAPI@cms.hhs.gov."
)

APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_EXPIRED_MESG = (
    "User data access grant expired. "
    "To refresh Medicare data, end user must re-authenticate "
    "and consent to share their data."
)

FHIR_CLIENT_CERTSTORE = env(
    "DJANGO_FHIR_CERTSTORE",
    os.path.join(BASE_DIR, os.environ.get("DJANGO_FHIR_CERTSTORE_REL", "../certstore")),
)

FHIR_SERVER = {
    "FHIR_URL": env("FHIR_URL", "https://fhir.backend.bluebutton.hhsdevcloud.us"),
    "CERT_FILE": os.path.join(
        FHIR_CLIENT_CERTSTORE, env("FHIR_CERT_FILE", "ca.cert.pem")
    ),
    "KEY_FILE": os.path.join(
        FHIR_CLIENT_CERTSTORE, env("FHIR_KEY_FILE", "ca.key.nocrypt.pem")
    ),
    "CLIENT_AUTH": True,
}

FHIR_POST_SEARCH_PARAM_IDENTIFIER_MBI_HASH = (
    "https://bluebutton.cms.gov/resources/identifier/mbi-hash"
)

FHIR_POST_SEARCH_PARAM_IDENTIFIER_HICN_HASH = (
    "https://bluebutton.cms.gov/resources/identifier/hicn-hash"
)

"""
    (mbi, hicn, etc); the following are all valid values for Identifier, and all might represent the same resource:
        - `identifier=https://bluebutton.cms.gov/resources/identifier/hicn-hash|<your hicn hash>`
        - `identifier=https://bluebutton.cms.gov/resources/identifier/mbi-hash|<your mbi hash>`
        - `identifier=http://hl7.org/fhir/sid/us-mbi|<your mbi>`
    example: "http://hl7.org/fhir/sid/us-mbi|<your mbi>"
"""

FHIR_PATIENT_SEARCH_PARAM_IDENTIFIER_MBI = (
    "http://hl7.org/fhir/sid/us-mbi"
)

FHIR_PARAM_FORMAT = "json"

# Timeout for request call
REQUEST_CALL_TIMEOUT = (30, 120)
# Headers Keep-Alive value
# this can be over-ridden in aws-{env}.py file to set values per environment
REQUEST_EOB_KEEP_ALIVE = "timeout=120, max=10"

SIGNUP_TIMEOUT_DAYS = env("SIGNUP_TIMEOUT_DAYS", 7)
ORGANIZATION_NAME = "CMS Medicare Blue Button"

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/v1/accounts/login"

LOGOUT_REDIRECT_URL = "/"

# Move Admin to a variable url location
ADMIN_PREPEND_URL = env("DJANGO_ADMIN_PREPEND_URL", "")

ALLOW_END_USER_EXTERNAL_AUTH = "B"
EXTERNAL_AUTH_NAME = "Medicare.gov"

# SLSx settings
SLSX_CLIENT_ID = env("DJANGO_SLSX_CLIENT_ID")
SLSX_CLIENT_SECRET = env("DJANGO_SLSX_CLIENT_SECRET")

# ACA token for SLSX_TOKEN_ENDPOINT
MEDICARE_SLSX_AKAMAI_ACA_TOKEN = env("DJANGO_MEDICARE_SLSX_AKAMAI_ACA_TOKEN", "")

MEDICARE_SLSX_REDIRECT_URI = env(
    "DJANGO_MEDICARE_SLSX_REDIRECT_URI", "http://localhost:8000/mymedicare/sls-callback"
)

MEDICARE_SLSX_LOGIN_URI = env(
    "DJANGO_MEDICARE_SLSX_LOGIN_URI",
    "https://test.medicare.gov/sso/authorize?client_id=bb2api",
)
SLSX_HEALTH_CHECK_ENDPOINT = env(
    "DJANGO_SLSX_HEALTH_CHECK_ENDPOINT", "https://test.accounts.cms.gov/health"
)
SLSX_TOKEN_ENDPOINT = env(
    "DJANGO_SLSX_TOKEN_ENDPOINT", "https://test.medicare.gov/sso/session"
)
SLSX_SIGNOUT_ENDPOINT = env(
    "DJANGO_SLSX_SIGNOUT_ENDPOINT", "https://test.medicare.gov/sso/signout"
)
SLSX_USERINFO_ENDPOINT = env(
    "DJANGO_SLSX_USERINFO_ENDPOINT", "https://test.accounts.cms.gov/v1/users"
)

# SSL verify for internal endpoints can't currently use SSL verification (this may change in the future)
SLSX_VERIFY_SSL_INTERNAL = env("DJANGO_SLSX_VERIFY_SSL_INTERNAL", False)
SLSX_VERIFY_SSL_EXTERNAL = env("DJANGO_SLSX_VERIFY_SSL_EXTERNAL", False)

# Message returned to bene for API exceptions related to medicare login/SLS
MEDICARE_ERROR_MSG = "An error occurred connecting to medicare.gov account"

AUTHENTICATION_BACKENDS = (
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesBackend",
    "apps.accounts.backends.EmailAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
)

# Change these for production
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
DEFAULT_SAMPLE_FHIR_ID = env("DJANGO_DEFAULT_SAMPLE_FHIR_ID", "-20140000008325")
TESTCLIENT_REDIRECT_URI = "/testclient/callback"

OFFLINE = False
EXTERNAL_LOGIN_TEMPLATE_NAME = "/v1/accounts/upstream-login"

BLOCK_HTTP_REDIRECT_URIS = False
IS_MEDIA_URL_LOCAL = False

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
    # Email config
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

# PROD Access Credentialing
# TTL (time to live, in minutes) for a bb2 generated unique and one time use url to be shared with on boarding app
# for obtaining app credentials i.e. client id and client secret
CREDENTIALS_REQUEST_URL_TTL = 5
