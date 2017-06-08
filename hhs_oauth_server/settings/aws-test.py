from .base import *
import os
import socket
import datetime
from getenv import env
from ..utils import bool_env

# Add testac to Dev/Test environments only
if 'apps.fhir.testac' not in INSTALLED_APPS:
    INSTALLED_APPS = INSTALLED_APPS + [
        'apps.fhir.testac',
    ]

# Set ADMINS and MANAGERS
ADMINS = (
    ('Mark Scrimshire[Test]', 'mark@ekivemark.com'),
)
MANAGERS = ADMINS

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS', ['*',
                                             socket.gethostname()])

# if ALLOWED_HOSTS == ['*', socket.gethostname()]:
#     print("WARNING: Set DJANGO_ALLOWED_HOSTS to the hostname "
#           "for Production operation.\n"
#           "         Currently defaulting to %s " % ALLOWED_HOSTS)
# Warning: on macOS hostname is case sensitive

# removing security enforcement in development mode
# DEBUG = True
DEBUG = bool_env(env('DJANGO_DEBUG', True))

if DEBUG:
    print("WARNING: Set DJANGO_DEBUG environment variable to False "
          "to run in production mode \n"
          "         and set DJANGO_ALLOWED_HOSTS to "
          "valid host names")

# Add apps for Site/Installation specific implementation here:
# The hhs_oauth_server.hhs_oauth_server_context

TEST_SPECIFIC_APPS = [
    # Installation/Site Specific apps based on  -----------------
    'storages',
]
INSTALLED_APPS += TEST_SPECIFIC_APPS

# AWS Credentials need to support SES, SQS and SNS
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', 'change-me')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY',
                            'change-me')

AWS_STORAGE_BUCKET_NAME = 'content-test-bbonfhir-com'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

STATICFILES_LOCATION = '/static/'
STATICFILES_STORAGE = 'hhs_oauth_server.s3_storage.StaticStorage'
STATIC_URL = "https://%s%s" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
# STATIC_URL = '/static/'

MEDIAFILES_LOCATION = 'media'
DEAFULT_FILE_STORAGE = 'hhs_oauth_server.s3_storage.MediaStorage'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
# MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'sitestatic'),
]

# emails
SEND_EMAIL = bool_env(env('DJANGO_SEND_EMAIL', True))
# If using AWS SES, the email below must first be verified.
DEFAULT_FROM_EMAIL = env('DJANGO_FROM_EMAIL', 'change-me@example.com')
# The console.EmailBackend backend prints to the console.
# Redefine this for SES or other email delivery mechanism
EMAIL_BACKEND_DEFAULT = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', EMAIL_BACKEND_DEFAULT)

# SMS
SEND_SMS = bool_env(env('DJANGO_SEND_SMS', False))

# MFA - Active or Not or False
# If using MFA enabled login this value is used to determin if
# reverse with mfa_login or reverse with login is called
#     if settings.MFA:
#         return HttpResponseRedirect(reverse('mfa_login'))
#     else:
#         return HttpResponseRedirect(reverse('login'))
MFA = True

# Add in apps.accounts backends for DEV environment
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'apps.accounts.auth.SettingsBackend',
    'apps.accounts.mymedicare_auth.MyMedicareBackend',
)

APPLICATION_TITLE = env('DJANGO_APPLICATION_TITLE', 'CMS Blue Button API [TEST]')

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
AXES_COOLOFF_TIME = datetime.timedelta(seconds=60)

ORGANIZATION_NAME = env('DJANGO_ORGANIZATION_NAME', 'CMS Blue Button API Server[TEST]')

# logging
# Based on blog posts:
# http://thegeorgeous.com/2015/02/27/Logging-into-multiple-files-in-Django.html
# https://docs.djangoproject.com/en/1.10/topics/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s '
                      '[%(process)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(name)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
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
            'filename': '/var/log/pyapps/debug.log',
        },
        'file_error': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': '/var/log/pyapps/error.log',
        },
        'file_info': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': '/var/log/pyapps/info.log',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_true'],
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'hhs_server': {
            'handlers': ['console', 'file_debug'],
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
        }

    },
}
