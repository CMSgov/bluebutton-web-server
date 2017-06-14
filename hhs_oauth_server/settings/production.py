from .base import *
from ..utils import bool_env

# security enforcement
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = bool_env(env('DJANGO_SECURE_SSL_REDIRECT', True))
SESSION_COOKIE_SECURE = bool_env(env('DJANGO_SESSION_COOKIE_SECURE', True))

# AWS
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')

# emails
EMAIL_BACKEND_DEFAULT = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', EMAIL_BACKEND_DEFAULT)
EMAIL_HOST = env('DJANGO_EMAIL_HOST')
EMAIL_PORT = env('DJANGO_EMAIL_HOST_PORT')
EMAIL_HOST_USER = env('DJANGO_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('DJANGO_EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = bool_env(env('DJANGO_EMAIL_USE_TLS', True))

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    # Add Check for SLS Authentication
    'apps.accounts.auth.SettingsBackend',
    # Add check for MyMedicare Login Hack
    'apps.accounts.mymedicare_auth.MyMedicareBackend',
)

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
        'unsuccessful_login': {
            'handlers': ['console', 'file_info'],
            'level': 'INFO',
        },
        'oauth2_provider': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'admin_interface': {
            'handlers': ['console', 'file_info'],
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
