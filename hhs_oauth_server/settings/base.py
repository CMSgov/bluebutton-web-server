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

# Set ADMINS and MANAGERS
# Override ADMINS and MANAGERS Settings in environment specific settings file
# or in custom-envvars.py
ADMINS = (
    ('Mark Scrimshire', 'mark@ekivemark.com'),
)
MANAGERS = ADMINS

# security
# SECRET_KEY = env('DJANGO_SECRET_KEY')
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

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS', ['*',
                                             socket.gethostname()])

# if ALLOWED_HOSTS == ['*', socket.gethostname()]:
#     print("WARNING: Set DJANGO_ALLOWED_HOSTS to the hostname "
#           "for Production operation.\n"
#           "         Currently defaulting to %s " % ALLOWED_HOSTS)
# Warning: on macOS hostname is case sensitive

# DEBUG = env('DJANGO_DEBUG', False)
DEBUG = bool_env(env('DJANGO_DEBUG', True))

# if DEBUG:
#     print("WARNING: Set DJANGO_DEBUG environment variable to False "
#           "to run in production mode \n"
#           "         and set DJANGO_ALLOWED_HOSTS to "
#           "valid host names")

# apps and middlewares
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 1st Party (in-house) ----------
    # Account related services
    'apps.accounts',
    # Define scopes and related protected resource URLs.
    'apps.capabilities',
    # /.well-known/ endpoints
    'apps.wellknown',

    # Endorsement example TODO migrate to reusable app
    'apps.endorse',

    # Use AppConfig to set apps.dot_ext to dot_ext so that splits in
    # django.db.models.utils doesn't have more than 2 values
    # There probably should be an edit to django.db so that the split
    # could deal with apps.dot_ext.model_name when it encounters a string
    'apps.dot_ext.apps.dot_extConfig',

    # Landing pages, etc.
    'apps.home',

    # FHIR Server
    # TODO - Add comment to each of these per main function
    'apps.fhir.fhir_core',
    'apps.fhir.server',
    'apps.fhir.bluebutton',
    'apps.fhir.build_fhir',
    'apps.fhir.fhir_consent',

    # Development Specific - Remove in production

    # TODO migrate to move to sandbox or apps.fhir.sandbox
    'apps.sandbox',

    # TODO Add comment. Should this be migrated elsewhere?
    'apps.fhir.testac',

    # TODO - Migrate to sandbox.  Add tests
    # 'apps.cmsblue',

    # 3rd Party ---------------------
    'corsheaders',
    'bootstrapform',
    'axes',
    # DOT must be installed after apps.dot_ext in order to override templates
    'oauth2_provider',

]

# Add apps for Site/Installation specific implementation here:
# The hhs_oauth_server.hhs_oauth_server_context

# CorsMiddleware needs to come before Django's
# CommonMiddleware if you are using Django's
# USE_ETAGS = True setting,
# otherwise the CORS headers will be lost from the 304 not-modified responses,
# causing errors in some browsers.
# See https://github.com/ottoyiu/django-cors-headers for more information.
MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = bool_env(env('CORS_ORIGIN_ALLOW_ALL', True))

ROOT_URLCONF = 'hhs_oauth_server.urls'

# TEMPLATES.context_processor:
# 'hhs_oauth_server.hhs_oauth_server_context.active_apps'
# enables custom code to be branched in templates eg.
#                 {% if "apps.extapi" in active_apps %}
#
#                     {%  include "extapi/get_started.html" %}
#                 {% endif %}
# Place all environment/installation specific code in a separate app
# hhs_oauth_server.hhs_oauth_server_context.py also
# includes IsAppInstalled to check for target_app in INSTALLED_APPS
# This enables implementation specific code to be branched inside views and
# functions.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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
        },
    },
]

WSGI_APPLICATION = 'hhs_oauth_server.wsgi.application'

# database configuration
if os.environ.get('DATABASES_CUSTOM'):
    DATABASES_DEFAULT = os.environ.get('DATABASES_CUSTOM')
else:
    DATABASES_DEFAULT = 'sqlite:///{}/db.sqlite3'.format(BASE_DIR)

DATABASES = {
    'default': dj_database_url.config(default=DATABASES_DEFAULT),
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
# Don't use BASE_DIR because for Production Environmnts
# Static Files may be located on an entirely different server.
# But the default can be BASE_DIR Setting
ASSETS_ROOT = env('DJANGO_ASSETS_ROOT', BASE_DIR)

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(ASSETS_ROOT, 'collectedstatic')
MEDIA_ROOT = os.path.join(ASSETS_ROOT, 'media')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'sitestatic'),
]

# emails
SEND_EMAIL = bool_env(env('DJANGO_SEND_EMAIL', True))
# If using AWS SES, the email below must first be verified.
DEFAULT_FROM_EMAIL = env('DJANGO_FROM_EMAIL', 'change-me@example.com')

# email backend options are:
# 'django.core.mail.backends.smtp.EmailBackend'
# 'django.core.mail.backends.filebased.EmailBackend'
# 'django.core.mail.backends.locmem.EmailBackend'
# 'django.core.mail.backends.dummy.EmailBackend'
# 'django_ses.SESBackend'

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

# Code from SMTP.py:
#         self.host = host or settings.EMAIL_HOST
#         self.port = port or settings.EMAIL_PORT
#         self.username = settings.EMAIL_HOST_USER if username is None else username
#         self.password = settings.EMAIL_HOST_PASSWORD if password is None else password
#         self.use_tls = settings.EMAIL_USE_TLS if use_tls is None else use_tls
#         self.use_ssl = settings.EMAIL_USE_SSL if use_ssl is None else use_ssl
#         self.timeout = settings.EMAIL_TIMEOUT if timeout is None else timeout
#         self.ssl_keyfile = settings.EMAIL_SSL_KEYFILE if ssl_keyfile is None else ssl_keyfile
#         self.ssl_certfile = settings.EMAIL_SSL_CERTFILE if ssl_certfile is None else ssl_certfile
#         if self.use_ssl and self.use_tls:
#             raise ValueError(
#                 "EMAIL_USE_TLS/EMAIL_USE_SSL are mutually exclusive, so only set "
#                 "one of those settings to True.")

# SMS
SEND_SMS = bool_env(env('DJANGO_SEND_SMS', False))

# MFA - Active or Not or False
# If using MFA enabled login this value is used to determine if
# reverse with mfa_login or reverse with login is called
#     if settings.MFA:
#         return HttpResponseRedirect(reverse('mfa_login'))
#     else:
#         return HttpResponseRedirect(reverse('login'))


MFA = True

# AWS Credentials need to support SES, SQS and SNS
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', 'change-me')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', 'change-me')

# logging
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
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        # 'lgfile': {
        #     'class': 'logging.FileHandler',
        #     'filename': 'logging.log',
        #     'mode': 'w',
        #     'formatter': 'verbose',
        # }
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
        'tests': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }

    },
}

# third parties
AUTH_PROFILE_MODULE = 'accounts.UserProfile'
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    # 'apps.accounts.auth.SettingsBackend',
    # 'apps.accounts.mymedicare_auth.MyMedicareBackend',
)

OAUTH2_PROVIDER_APPLICATION_MODEL = 'dot_ext.Application'
# removing apps. by using AppConfig for apps.dot_ext
OAUTH2_PROVIDER = {
    'OAUTH2_VALIDATOR_CLASS': 'apps.dot_ext.oauth2_validators.'
                              'SingleAccessTokenValidator',
    'OAUTH2_SERVER_CLASS': 'apps.dot_ext.oauth2_server.Server',
    'SCOPES_BACKEND_CLASS': 'apps.dot_ext.scopes.CapabilitiesScopes',
}

# These choices will be available in the expires_in field
# of the oauth2 authorization page.
DOT_EXPIRES_IN = (
    (86400 * 365 * 100, _('Forever')),
    (86400, _('1 Day')),
    (86400 * 7, _('1 Week')),
    (86400 * 365, _('1 Year')),
)


# Set the theme
THEME = THEMES[THEME_SELECTED]

APPLICATION_TITLE = env('DJANGO_APPLICATION_TITLE', 'CMS Blue Button API')

HOSTNAME_URL = env('HOSTNAME_URL', 'http://localhost:8000')
INVITE_REQUEST_ADMIN = env('DJANGO_INVITE_REQUEST_ADMIN')

# Set the default Encoding standard. typically 'utf-8'
ENCODING = 'utf-8'

# LINKS TO DOCS
USER_DOCS = "http://transparenthealth.github.io/beneficiary-help/"
USER_DOCS_TITLE = "Beneficiary Help"
DEVELOPER_DOCS = "https://transparenthealth.github.io/blue-button-developer-docs/"
DEVELOPER_DOCS_TITLE = "Developer Documentation"

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
    'USER_DOCS',
    'USER_DOCS_TITLE',
    'DEVELOPER_DOCS',
    'DEVELOPER_DOCS_TITLE'
]


# Make sessions die out fast for more security ------------------
# Logout after 30 minutes of inactivity
SESSION_COOKIE_AGE = 1800
# Logout if the browser is closed
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


# Stub for Custom Authentication Backend
SLS_USER = env('DJANGO_SLS_USER')
# enclose value for DJANGO_SLS_PASSWORD in single quotes to preserve
# special characters eg. $
# eg. export DJANGO_SLS_PASSWORD='$pecial_CharacterPre$erved'
SLS_PASSWORD = env('DJANGO_SLS_PASSWORD')
SLS_FIRST_NAME = env('DJANGO_SLS_FIRST_NAME')
SLS_LAST_NAME = env('DJANGO_SLS_LAST_NAME')
SLS_EMAIL = env('DJANGO_SLS_EMAIL')

# Failed Login Attempt Module: AXES
# Either integer or timedelta.
# If integer interpreted, as hours
AXES_COOLOFF_TIME = datetime.timedelta(seconds=600)
LOGIN_RATE = '10/m'
# Default FHIR Server if none defined in Crosswalk or FHIR Server model
# We will need to add REWRITE_FROM and REWRITE_TO to models
# to enable search and replace in content returned from backend server.
# Otherwise source server address is exposed to external users.

BB_CONSENT = {
    'AGREEMENT_URL': "/consent/agreement/1/",
    'URL_TITLE': "CMS Blue Button Beneficiary-Application Consent Agreement",
    'POLICY_URL': "/consent/policy/1/"
}

FHIR_SERVER_CONF = {'SERVER': env('THS_FHIR_SERVER'),
                    'PATH': env('THS_FHIR_PATH'),
                    'RELEASE': env('THS_FHIR_RELEASE'),
                    'REWRITE_FROM': env('THS_FHIR_REWRITE_FROM'),
                    # RERITE_FROM should be a list
                    'REWRITE_TO': env('THS_FHIR_REWRITE_TO'),
                    # Minutes until search expires
                    'SEARCH_EXPIRY': env('THS_SEARCH_EXPIRY', 30)}

FHIR_CLIENT_CERTSTORE = env('DJANGO_FHIR_CERTSTORE',
                            os.path.join(BASE_DIR, '../certstore'))

# cert_file and key_file are referenced relative to BASE_DIR/../certstore
# used by FhirServer_Auth()
FHIR_DEFAULT_AUTH = {'client_auth': False,
                     'cert_file': '',
                     'key_file': ''}

SIGNUP_TIMEOUT_DAYS = env('SIGNUP_TIMEOUT_DAYS', 7)
ORGANIZATION_NAME = env('DJANGO_ORGANIZATION_NAME', 'CMS Blue Button API')

LOGIN_REDIRECT_URL = '/accounts/mfa/login'
LOGIN_URL = '/accounts/mfa/login'

REQUIRE_AUTHORIZE_APP_FLAG = False
