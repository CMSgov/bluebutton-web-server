from .base import *

# removing security enforcement in development mode
DEBUG = True
SECRET_KEY = env('DJANGO_SECRET_KEY', '1234567890')

HOSTNAME_URL = env('HOSTNAME_URL', 'http://127.0.0.1:8000')
# HOSTNAME_URL = env('HOSTNAME_URL', 'http://192.168.0.187:8000')
# note: if localhost is used instead of IP, run into session overriden issue (don't know why),
# the sympton is KeyError when get client_id from session;
# use IP instead works fine

DEV_SPECIFIC_APPS = [
    # Installation/Site Specific apps based on  -----------------
    # 'storages',
    # A test client - moved to aws-test / dev /impl settings
    'apps.testclient',

]
INSTALLED_APPS += DEV_SPECIFIC_APPS

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/')],
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

# needed to support use of http for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

OAUTH2_PROVIDER = {
    'OAUTH2_VALIDATOR_CLASS': 'apps.dot_ext.oauth2_validators.'
                              'SingleAccessTokenValidator',
    'OAUTH2_SERVER_CLASS': 'apps.dot_ext.oauth2_server.Server',
    'SCOPES_BACKEND_CLASS': 'apps.dot_ext.scopes.CapabilitiesScopes',
    'OAUTH2_BACKEND_CLASS': 'apps.dot_ext.oauth2_backends.OAuthLibSMARTonFHIR',
    'ALLOWED_REDIRECT_URI_SCHEMES': ['https', 'http']
}

# IF a new file is added for logging go to hhs_ansible and update configuration
# script to touch log files:
# hhs_ansible/playbook/appserver/roles/app_update/tasks/main.yml
# add the new filename as an item to the "Create the log files" action
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
        },
        'perf_mon': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': '/var/log/pyapps/perf_mon.log',
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
            'handlers': ['console'],   # 'perf_mon'],
            'level': 'INFO',
        },
        'performance': {
            'handlers': ['console'],   # 'perf_mon'],
            'level': 'INFO',
        }
    },
}
