from .base import *
import os
import socket
from getenv import env
from ..utils import bool_env

ADMINS = (
    ('Mark Scrimshire[Dev]', 'mark@ekivemark.com'),
)
MANAGERS = ADMINS

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS', ['*', socket.gethostname()])

# Add apps for Site/Installation specific implementation here:
# The hhs_oauth_server.hhs_oauth_server_context

DEV_SPECIFIC_APPS = [
    # Installation/Site Specific apps based on  -----------------
    'storages',
    # A test client - moved to aws-test / dev /impl settings
    'apps.testclient',
]
INSTALLED_APPS += DEV_SPECIFIC_APPS

OPTIONAL_INSTALLED_APPS += ["testclient", ]

# AWS Credentials need to support SES, SQS and SNS
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', 'change-me')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY',
                            'change-me')

AWS_STORAGE_BUCKET_NAME = 'content-dev-bbonfhir-com'
AWS_S3_CUSTOM_DOMAIN = 's3.amazonaws.com/%s' % AWS_STORAGE_BUCKET_NAME

STATICFILES_LOCATION = '/static/'
STATICFILES_STORAGE = 'hhs_oauth_server.s3_storage.StaticStorage'
STATIC_URL = "https://%s%s" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
# STATIC_URL = '/static/'
# print("Static URL:%s" % STATIC_URL)

MEDIAFILES_LOCATION = '/media/'
DEAFULT_FILE_STORAGE = 'hhs_oauth_server.s3_storage.MediaStorage'
MEDIA_URL = "https://%s%s" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
# MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(ASSETS_ROOT, 'collectedstatic')
MEDIA_ROOT = os.path.join(ASSETS_ROOT, 'media')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'sitestatic'),
]

OAUTH2_AUTHORIZATION_FORM = 'authorize/default.html'

# Place all environment/installation specific code in a separate app
# hhs_oauth_server.hhs_oauth_server_context.py also
# includes IsAppInstalled to check for target_app in INSTALLED_APPS
# This enables implementation specific code to be branched inside views and
# functions.
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

# emails
SEND_EMAIL = bool_env(env('DJANGO_SEND_EMAIL', True))
# If using AWS SES, the email below must first be verified.
DEFAULT_FROM_EMAIL = env('DJANGO_FROM_EMAIL', 'bluebutton.dev@fhirservice.net')
# The console.EmailBackend backend prints to the console.
# Redefine this for SES or other email delivery mechanism
EMAIL_BACKEND_DEFAULT = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', EMAIL_BACKEND_DEFAULT)

# SMS
SEND_SMS = bool_env(env('DJANGO_SEND_SMS', True))

MFA = True

# Add in apps.accounts backends for DEV environment
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'apps.accounts.auth.SettingsBackend',
)

APPLICATION_TITLE = env('DJANGO_APPLICATION_TITLE', 'CMS Blue Button API [DEV]')

# Should be set to True in production and False in all other dev and test environments
REQUIRE_HTTPS_REDIRECT_URIS = False

#
# MyMedicare Authentication Integration
#
SLS_TOKEN_ENDPOINT = env('DJANGO_SLS_TOKEN_ENDPOINT')
MEDICARE_LOGIN_URI = env('DJANGO_MEDICARE_LOGIN_URI')
MEDICARE_REDIRECT_URI = env('DJANGO_MEDICARE_REDIRECT_URI')
MEDICARE_LOGIN_TEMPLATE_NAME = env('DJANGO_MEDICARE_LOGIN_TEMPLATE_NAME')
AUTHORIZATION_TEMPLATE_NAME = env('DJANGO_AUTHORIZATION_TEMPLATE_NAME')
if env('DJANGO_SLS_VERIFY_SSL'):
    if env('DJANGO_SLS_VERIFY_SSL').lower() == "true":
        SLS_VERIFY_SSL = True
    else:
        SLS_VERIFY_SSL = False
else:
    SLS_VERIFY_SSL = False


# Fixed user and password for fake backend
SETTINGS_AUTH_USER = 'ben'
SETTINGS_AUTH_PASSWORD = 'pbkdf2_sha256$24000$V6XjGqYYNGY7$13tFC13aaTohxBgP2W3glTBz6PSbQN4l6HmUtxQrUys='

ORGANIZATION_NAME = env('DJANGO_ORGANIZATION_NAME', 'CMS Blue Button API Server[DEV]')

# logging
# Based on blog posts:
# http://thegeorgeous.com/2015/02/27/Logging-into-multiple-files-in-Django.html
# https://docs.djangoproject.com/en/1.10/topics/logging/
# IF a new file is added for logging go to hhs_ansible and update configuration
# script to touch log files:
# hhs_ansible/playbook/appserver/roles/app_update/tasks/main.yml
# add the new filename as an item to the "Create the log files" action
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name)s '
                      '[%(process)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'jsonout': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", '
                      '"name": "%(name)s", "message": "%(message)s"}',
            'datefmt': '%Y-%m-%d %H:%M:%S'

        }
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'simple',
            'filename': '/var/log/pyapps/debug.log',
        },
        'file_error': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': '/var/log/pyapps/error.log',
        },
        'file_info': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'formatter': 'simple',
            'filename': '/var/log/pyapps/info.log',
        },
        'badlogin_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'simple',
            'filename': '/var/log/pyapps/login_failed.log',
        },
        'adminuse_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'simple',
            'filename': '/var/log/pyapps/admin_access.log',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose'
        },
        'perf_mon': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'jsonout',
            'filename': '/var/log/pyapps/perf_mon.log',
        }
    },
    'loggers': {
        'hhs_server': {
            'handlers': ['console', 'file_debug'],
            'level': 'DEBUG',
        },
        'hhs_oauth_server.accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'hhs_server_debug': {
            'handlers': ['console', 'file_debug'],
            'level': 'DEBUG',
        },
        'hhs_server_error': {
            'handlers': ['console', 'file_error', 'mail_admins'],
            'level': 'ERROR',
        },
        'unsuccessful_logins': {
            'handlers': ['console', 'badlogin_info'],
            'level': 'INFO',
        },
        'admin_interface': {
            'handlers': ['console', 'adminuse_info'],
            'level': 'INFO',
        },
        'hhs_server_info': {
            'handlers': ['console', 'file_info'],
            'level': 'INFO',
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
        },
        'performance': {
            'handlers': ['console', 'perf_mon'],
            'level': 'INFO',
        }
    },
}
