import os
import dj_database_url
import socket
import datetime
from getenv import env
from ..utils import bool_env, int_env

from django.contrib.messages import constants as messages
from django.utils.translation import ugettext_lazy as _
from .themes import THEMES, THEME_SELECTED

# project root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(BASE_DIR, '..')

# security
SECRET_KEY = env('DJANGO_SECRET_KEY',
                 'FAKE_SECRET_KEY_YOU_MUST_SET_DJANGO_SECRET_KEY_VAR')
if SECRET_KEY == 'FAKE_SECRET_KEY_YOU_MUST_SET_DJANGO_SECRET_KEY_VAR':
    print("WARNING: Generate your secret key and set in environment "
          "variable: DJANGO_SECRET_KEY")

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'NumericPasswordValidator',
    },
]

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS', ['*', socket.gethostname()])

DEBUG = True
APPEND_SLASH = False

# apps and middlewares
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',

    # 1st Party (in-house) ----------
    'apps.accounts',
    'apps.capabilities',
    'apps.wellknown',
    'apps.health',

    # Use AppConfig to set apps.dot_ext to dot_ext so that splits in
    # django.db.models.utils doesn't have more than 2 values
    # There probably should be an edit to django.db so that the split
    # could deal with apps.dot_ext.model_name when it encounters a string
    'apps.dot_ext.apps.dot_extConfig',
    'apps.home',
    'apps.fhir.server',
    'apps.fhir.bluebutton',
    'apps.mymedicare_cb',

    # 3rd Party ---------------------
    'corsheaders',
    'bootstrapform',
    # DOT must be installed after apps.dot_ext in order to override templates
    'oauth2_provider',
    'axes',

]

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'token': env('TOKEN_THROTTLE_RATE', '100000/s'),
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
OPTIONAL_INSTALLED_APPS = ["", ]

MIDDLEWARE_CLASSES = [
    # Middleware that adds headers to the resposne
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'hhs_oauth_server.request_logging.RequestTimeLoggingMiddleware',
    'corsheaders.middleware.CorsMiddleware',

    # Middleware that can send a response must be below this line
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.dot_ext.throttling.ThrottleMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = bool_env(env('CORS_ORIGIN_ALLOW_ALL', True))

ROOT_URLCONF = 'hhs_oauth_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, ('templates/'))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
                'hhs_oauth_server.hhs_oauth_server_context.active_apps',
            ],
            'builtins': [
            ],
        },
    },
]

WSGI_APPLICATION = 'hhs_oauth_server.wsgi.application'

CACHES = {
    'default': {
        'BACKEND': os.environ.get('CACHE_BACKEND', 'django.core.cache.backends.db.DatabaseCache'),
        'LOCATION': os.environ.get('CACHE_LOCATION', 'django_cache'),
    },
}

DATABASES = {
    'default': dj_database_url.config(default=env('DATABASES_CUSTOM',
                                                  'sqlite:///{}/db.sqlite3'.format(BASE_DIR))),
}

# this helps Django messages format nicely with Bootstrap3
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# static files and media
ASSETS_ROOT = env('DJANGO_ASSETS_ROOT', BASE_DIR)

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(ASSETS_ROOT, 'collectedstatic')
MEDIA_ROOT = os.path.join(ASSETS_ROOT, 'media')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'sitestatic'),
]


# emails
DEFAULT_FROM_EMAIL = env('DJANGO_FROM_EMAIL', 'change-me@example.com')
DEFAULT_ADMIN_EMAIL = env('DJANGO_ADMIN_EMAIL', 'change-me@example.com')

# The console.EmailBackend backend prints to the console.
# Redefine this for SES or other email delivery mechanism
EMAIL_BACKEND_DEFAULT = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', EMAIL_BACKEND_DEFAULT)
EMAIL_HOST = env('DJANGO_EMAIL_HOST', 'email-smtp.us-east-1.amazonaws.com')
# SES PORT options: 25, 465, 587, 2465 or 2587.
# Port 25 is throttled
# Use port 587 or 2587 for TLS connections
# Use port 465 or 2465 for Native SSL support
EMAIL_PORT = int_env(env('DJANGO_EMAIL_PORT', 587))
EMAIL_USE_TLS = bool_env(env('DJANGO_EMAIL_USE_TLS', 'True'))
EMAIL_USE_SSL = bool_env(env('DJANGO_EMAIL_USE_SSL', 'False'))
EMAIL_TIMEOUT = env('DJANGO_EMAIL_TIMEOUT', None)
EMAIL_HOST_USER = env('DJANGO_EMAIL_HOST_USER', None)
EMAIL_HOST_PASSWORD = env('DJANGO_EMAIL_HOST_PASSWORD', None)
EMAIL_SSL_KEYFILE = env('DJANGO_EMAIL_SSL_KEYFILE', None)
EMAIL_SSL_CERTFILE = env('DJANGO_EMAIL_SSL_CERTFILE', None)

MFA = True

# AWS Credentials need to support SES, SQS and SNS
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', 'change-me')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', 'change-me')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s '
                      '[%(process)d] %(name)s line:%(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        },
        'jsonout': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", '
                      '"name": "%(name)s", "message": "%(message)s"}',
            'datefmt': '%Y-%m-%d %H:%M:%S'

        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'hhs_server': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'hhs_oauth_server.accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'oauth2_provider': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'oauthlib': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'unsuccessful_logins': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'admin_interface': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'tests': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'audit': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'performance': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    },
}

AUTH_PROFILE_MODULE = 'accounts.UserProfile'

# Django Oauth Tookit settings and customizations
OAUTH2_PROVIDER_APPLICATION_MODEL = 'dot_ext.Application'
OAUTH2_PROVIDER = {
    'OAUTH2_VALIDATOR_CLASS': 'apps.dot_ext.oauth2_validators.'
                              'SingleAccessTokenValidator',
    'OAUTH2_SERVER_CLASS': 'apps.dot_ext.oauth2_server.Server',
    'SCOPES_BACKEND_CLASS': 'apps.dot_ext.scopes.CapabilitiesScopes',
    'OAUTH2_BACKEND_CLASS': 'apps.dot_ext.oauth2_backends.OAuthLibSMARTonFHIR',
    'ALLOWED_REDIRECT_URI_SCHEMES': ['https', 'http']
}

# These choices will be available in the expires_in field
# of the oauth2 authorization page.
DOT_EXPIRES_IN = (
    (86400 * 365 * 5, _('5 Years')),
    (86400, _('1 Day')),
    (86400 * 7, _('1 Week')),
    (86400 * 365, _('1 Year')),
    (86400 * 365 * 3, _('3 Years')),
    (86400 * 365 * 10, _('10 Years')),
    (86400 * 365 * 100, _('Forever')),
)

GRANT_AUTHORIZATION_CODE = "authorization-code"
GRANT_IMPLICIT = "implicit"
GRANT_TYPES = (
    (GRANT_AUTHORIZATION_CODE, _("Authorization code")),
    (GRANT_IMPLICIT, _("Implicit")),
)

# Set the theme
THEME = THEMES[THEME_SELECTED]


APPLICATION_TITLE = env('DJANGO_APPLICATION_TITLE',
                        'Blue Button 2.0')
ORGANIZATION_TITLE = env(
    'DJANGO_ORGANIZATION_TITLE',
    'The U.S. Centers for Medicare & Medicaid Services (CMS)')
ORGANIZATION_URI = env('DJANGO_ORGANIZATION_URI', 'https://cms.gov')
POLICY_URI = env(
    'DJANGO_POLICY_URI',
    'https://www.cms.gov/About-CMS/Agency-Information/Aboutwebsite/Privacy-Policy.html')
POLICY_TITLE = env('DJANGO_POLICY_TITLE', 'Privacy Policy')
TOS_URI = env('DJANGO_TOS_URI', 'https://bluebutton.cms.gov/terms')
TOS_TITLE = env('DJANGO_TOS_TITLE', 'Terms of Service')
TAG_LINE_1 = env('DJANGO_TAG_LINE_1', 'Share your Medicare data')
TAG_LINE_2 = env('DJANGO_TAG_LINE_2',
                 'with applications, organizations, and people you trust.')
EXPLAINATION_LINE = 'This service allows Medicare beneficiaries to connect their health data to applications of their choosing.'
EXPLAINATION_LINE = env('DJANGO_EXPLAINATION_LINE ', EXPLAINATION_LINE)

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

DISCLOSURE_TEXT = env('DJANGO_PRIVACY_POLICY_URI', DEFAULT_DISCLOSURE_TEXT)

HOSTNAME_URL = env('HOSTNAME_URL', 'http://localhost:8000')
INVITE_REQUEST_ADMIN = env('DJANGO_INVITE_REQUEST_ADMIN')
REQUIRE_INVITE_TO_REGISTER = env('REQUIRE_INVITE_TO_REGISTER', False)

# Set the default Encoding standard. typically 'utf-8'
ENCODING = 'utf-8'

TEALIUM_ENV = env('DJANGO_TEALIUM_ENV', 'dev')

# include settings values in SETTING_EXPORT to use values in Templates.
# eg. {{ settings.APPLICATION_TITLE }}
SETTINGS_EXPORT = [
    'DEBUG',
    'ALLOWED_HOSTS',
    'APPLICATION_TITLE',
    'THEME',
    'STATIC_URL',
    'STATIC_ROOT',
    'MFA',
    'DEVELOPER_DOCS_URI',
    'DEVELOPER_DOCS_TITLE',
    'ORGANIZATION_TITLE',
    'POLICY_URI',
    'POLICY_TITLE',
    'DISCLOSURE_TEXT',
    'TOS_URI',
    'TOS_TITLE',
    'TAG_LINE_1',
    'TAG_LINE_2',
    'EXPLAINATION_LINE',
    'EXTERNAL_AUTH_NAME',
    'ALLOW_END_USER_EXTERNAL_AUTH',
    'OPTIONAL_INSTALLED_APPS',
    'INSTALLED_APPS',
    'REQUIRE_INVITE_TO_REGISTER',
    'TEALIUM_ENV',
]

SESSION_COOKIE_AGE = 5400
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

FHIR_SERVER_DEFAULT = env('DJANGO_FHIRSERVER_ID', 1)

FHIR_SERVER_CONF = {'SERVER': env('THS_FHIR_SERVER'),
                    'PATH': env('THS_FHIR_PATH'),
                    'RELEASE': env('THS_FHIR_RELEASE'),
                    # REWRITE_FROM should be a list
                    'REWRITE_FROM': env('THS_FHIR_REWRITE_FROM'),
                    'REWRITE_TO': env('THS_FHIR_REWRITE_TO'),
                    # Minutes until search expires
                    'SEARCH_EXPIRY': env('THS_SEARCH_EXPIRY', 30)}

FHIR_CLIENT_CERTSTORE = env('DJANGO_FHIR_CERTSTORE',
                            os.path.join(BASE_DIR, '../certstore'))

# Timeout for request call
REQUEST_CALL_TIMEOUT = (30, 120)
# Headers Keep-Alive value
# this can be over-ridden in aws-{env}.py file to set values per environment
REQUEST_EOB_KEEP_ALIVE = "timeout=120, max=10"

SIGNUP_TIMEOUT_DAYS = env('SIGNUP_TIMEOUT_DAYS', 7)
ORGANIZATION_NAME = 'CMS Medicare Blue Button'

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/v1/accounts/mfa/login'

REQUIRE_AUTHORIZE_APP_FLAG = False

# Move Admin to a variable url location
ADMIN_PREPEND_URL = env('DJANGO_ADMIN_PREPEND_URL', '')

ALLOW_END_USER_EXTERNAL_AUTH = "B"
EXTERNAL_AUTH_NAME = 'MyMedicare.gov'

MEDICARE_LOGON = True
MEDICARE_LOGIN_URI = env('DJANGO_MEDICARE_LOGIN_URI ',
                         'https://dev2.account.mymedicare.gov/?scope=openid%20profile&client_id=bluebutton')
MEDICARE_REDIRECT_URI = env(
    'DJANGO_MEDICARE_REDIRECT_URI', 'http://localhost:8000/mymedicare/sls-callback')
SLS_USERINFO_ENDPOINT = env(
    'DJANGO_SLS_USERINFO_ENDPOINT', 'https://dev.accounts.cms.gov/v1/oauth/userinfo')
SLS_TOKEN_ENDPOINT = env(
    'DJANGO_SLS_TOKEN_ENDPOINT', 'https://dev.accounts.cms.gov/v1/oauth/token')


# Since this is internal False may be acceptable.
SLS_VERIFY_SSL = env('DJANGO_SLS_VERIFY_SSL', True)

AUTHENTICATION_BACKENDS = ('apps.accounts.email_auth_backend.EmailBackend',
                           'django.contrib.auth.backends.ModelBackend')

# Change these for production
USER_ID_SALT = env('DJANGO_USER_ID_SALT', "6E6F747468657265616C706570706572")
USER_ID_ITERATIONS = int(env("DJANGO_USER_ID_ITERATIONS", "2"))

USER_ID_TYPE_CHOICES = (('H', 'HICN'),
                        ('M', 'MBI'),
                        ('S', 'SSN'))

USER_ID_TYPE_DEFAULT = "H"
DEFAULT_SAMPLE_FHIR_ID = "20140000008325"
OFFLINE = False
EXTERNAL_LOGIN_TEMPLATE_NAME = '/v1/accounts/upstream-login'

BLOCK_HTTP_REDIRECT_URIS = False
