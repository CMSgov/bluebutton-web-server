import os
import dj_database_url
import socket
import datetime
from getenv import env

from django.contrib.messages import constants as messages
from django.utils.translation import ugettext_lazy as _

# project root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(BASE_DIR, '..')

# Set ADMINS and MANAGERS
ADMINS = (
    os.environ.get('DJANGO_APP_ADMINS', "('Mark Scrimshire', 'mark@ekivemark.com')"),
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
DEBUG = env('DJANGO_DEBUG', True)

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
    # Blue Button Text file parsing code
    'apps.cmsblue',
    # Endorsement example
    'apps.endorse',
    # Use AppConfig to set apps.dot_ext to dot_ext so that splits in
    # django.db.models.utils doesn't have more than 2 values
    # There probably should be an edit to django.db so that the split
    # could deal with apps.dot_ext.model_name when it encounters a string
    'apps.dot_ext.apps.dot_extConfig',
    # MyMedicare.gov Enhanced Validated Identity Linkage
    'apps.eimm',
    # Landing pages, etc.
    'apps.home',
    'apps.education',
    'apps.fhir.core',
    'apps.fhir.server',
    'apps.fhir.bluebutton',
    'apps.fhir.build_fhir',

    # 3rd Party ---------------------
    'corsheaders',
    'bootstrapform',
    'axes',
    # DOT must be installed after apps.dot_ext in order to override templates
    'oauth2_provider',
]

# Add apps for Site/Installation specific implementation here:
# The hhs_oauth_server.hhs_oauth_server_context

INSTALLATION_SPECIFIC_APPS = [
    # Installation/Site Specific apps based on  -----------------
    'apps.extapi',
]
INSTALLED_APPS += INSTALLATION_SPECIFIC_APPS

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

CORS_ORIGIN_ALLOW_ALL = env('CORS_ORIGIN_ALLOW_ALL', True)

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
SEND_EMAIL = env('DJANGO_SEND_EMAIL', True)
# If using AWS SES, the email below must first be verified.
DEFAULT_FROM_EMAIL = env('DJANGO_FROM_EMAIL', 'change-me@example.com')
# The console.EmailBackend backend prints to the console.
# Redefine this for SES or other email delivery mechanism
EMAIL_BACKEND_DEFAULT = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', EMAIL_BACKEND_DEFAULT)

# SMS
SEND_SMS = env('DJANGO_SEND_SMS', False)

# MFA - Active or Not or False
# If using MFA enabled login this value is used to determin if
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
            'format': '%(levelname)s %(asctime)s %(name)s '
                      '[%(process)d] %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(name)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'hhs_server': {
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
    'apps.accounts.auth.SettingsBackend',
    'apps.accounts.mymedicare_auth.MyMedicareBackend',
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
    (86400, _('1 Day')),
    (86400 * 7, _('1 Week')),
    (86400 * 365, _('1 Year')),
    (86400 * 365 * 100, _('Forever')),
)

# theme selection
THEMES = {
    0: {
        'NAME': 'Default-Readable',
        'PATH': 'theme/default/',
        'INFO': 'Readable san-serif base theme',
    },
    3: {
        'NAME': 'Readable',
        'PATH': 'theme/readable/',
        'INFO': 'Easy to read Bootswatch Theme',
    },
    4: {
        'NAME': 'Cerulean',
        'PATH': 'theme/cerulean/',
        'INFO': 'Blue Bootswatch theme theme',
    },
    5: {
        'NAME': 'Cosmo',
        'PATH': 'theme/cosmo/',
        'INFO': 'Cosmo bootswatch theme',
    },
    6: {
        'NAME': 'Cyborg',
        'PATH': 'theme/cyborg/',
        'INFO': 'Cyborg bootswatch theme',
    },
    7: {
        'NAME': 'Darkly',
        'PATH': 'theme/darkly/',
        'INFO': 'Darkly bootswatch theme',
    },
    8: {
        'NAME': 'Flatly',
        'PATH': 'theme/flatly/',
        'INFO': 'Flatly bootswatch theme',
    },
    9: {
        'NAME': 'Journal',
        'PATH': 'theme/journal/',
        'INFO': 'Journal bootswatch theme',
    },
    10: {
        'NAME': 'Lumen',
        'PATH': 'theme/lumen/',
        'INFO': 'Lumen bootswatch theme',
    },
    11: {
        'NAME': 'Paper',
        'PATH': 'theme/paper/',
        'INFO': 'Paper bootswatch theme',
    },
    12: {
        'NAME': 'Sandstone',
        'PATH': 'theme/sandstone/',
        'INFO': 'Sandstone bootswatch theme',
    },
    13: {
        'NAME': 'Simplex',
        'PATH': 'theme/simplex/',
        'INFO': 'Simplex bootswatch theme',
    },
    14: {
        'NAME': 'Slate',
        'PATH': 'theme/slate/',
        'INFO': 'Slate bootswatch theme',
    },
    15: {
        'NAME': 'Spacelab',
        'PATH': 'theme/spacelab/',
        'INFO': 'Spacelab bootswatch theme',
    },
    16: {
        'NAME': 'Superhero',
        'PATH': 'theme/superhero/',
        'INFO': 'Superhero bootswatch theme',
    },
    17: {
        'NAME': 'United',
        'PATH': 'theme/united/',
        'INFO': 'United bootswatch theme',
    },
    18: {
        'NAME': 'Yeti',
        'PATH': 'theme/yeti/',
        'INFO': 'Yeti bootswatch theme',
    },
    'SELECTED': env('DJANGO_SELECTED_THEME', 0),
}

if THEMES['SELECTED'] not in THEMES:
    THEME_SELECTED = 0
else:
    THEME_SELECTED = THEMES['SELECTED']

THEME = THEMES[THEME_SELECTED]

APPLICATION_TITLE = env('DJANGO_APPLICATION_TITLE', 'CMS Blue Button API')

HOSTNAME_URL = env('HOSTNAME_URL', '127.0.0.1:8000')
INVITE_REQUEST_ADMIN = env('DJANGO_INVITE_REQUEST_ADMIN')

# Set the default Encoding standard. typically 'utf-8'
ENCODING = 'utf-8'

# include settings values in SETTING_EXPORT to use values in Templates.
# eg. {{ settings.APPLICATION_TITLE }}
SETTINGS_EXPORT = [
    'DEBUG',
    'APPLICATION_TITLE',
    'THEME',
    'STATIC_URL',
    'MFA'
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

# Default FHIR Server if none defined in Crosswalk or FHIR Server model
# We will need to add REWRITE_FROM and REWRITE_TO to models
# to enable search and replace in content returned from backend server.
# Otherwise source server address is exposed to external users.

FHIR_SERVER_CONF = {'SERVER': env('THS_FHIR_SERVER'),
                    'PATH': env('THS_FHIR_PATH'),
                    'RELEASE': env('THS_FHIR_RELEASE'),
                    'REWRITE_FROM': env('THS_FHIR_REWRITE_FROM'),
                    # RERITE_FROM should be a list
                    'REWRITE_TO': env('THS_FHIR_REWRITE_TO'),
                    # Minutes until search expires
                    'SEARCH_EXPIRY': env('THS_SEARCH_EXPIRY', 30)}

SIGNUP_TIMEOUT_DAYS = env('SIGNUP_TIMEOUT_DAYS', 3)
ORGANIZATION_NAME = env('DJANGO_ORGANIZATION_NAME', 'CMS OAuth2 Server')
