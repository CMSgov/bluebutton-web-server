from .test import *

# Use env-specific logging config if present
LOGGING = env("DJANGO_LOGGING", {
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
            'format': '{"env": "' + env('TARGET_ENV', 'DEV') + '", "time": "%(asctime)s", "level": "%(levelname)s", '
                      '"name": "%(name)s", "message": "%(message)s"}',
            'datefmt': '%Y-%m-%d %H:%M:%S'

        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/code/docker-compose/tmp/bb2_logging_test.log',
        },
    },
    'loggers': {
        'hhs_server': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'hhs_oauth_server.accounts': {
            'handlers': ['console'],
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
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'performance': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    },
})
