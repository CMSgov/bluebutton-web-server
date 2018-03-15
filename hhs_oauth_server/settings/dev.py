from .base import *

# removing security enforcement in development mode
DEBUG = True
SECRET_KEY = env('DJANGO_SECRET_KEY', '1234567890')

HOSTNAME_URL = env('HOSTNAME_URL', 'http://127.0.0.1:8000')
INVITE_REQUEST_ADMIN = env(
    'DJANGO_INVITE_REQUEST_ADMIN', 'change-me@example.com')

ALLOW_CHOOSE_LOGIN = True

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


FHIR_SERVER_DEFAULT = env('DJANGO_FHIRSERVER_ID', 1)

# overrides FHIR server configuration with fake values
FHIR_SERVER_CONF = {
    'SERVER': env('THS_FHIR_SERVER', 'http://fhir.bbonfhir.com/'),
    'PATH': env('THS_FHIR_PATH', 'fhir-p/'),
    'RELEASE': env('THS_FHIR_RELEASE', 'baseDstu2/'),
    # REWRITE_FROM should be defined as a list
    'REWRITE_FROM': env('THS_FHIR_REWRITE_FROM', ['http://ec2-52-4-198-86.compute-1.amazonaws.com:8080/baseDstu2', ]),
    'REWRITE_TO': env('THS_FHIR_REWRITE_TO', 'http://localhost:8000/bluebutton/fhir/v1'),
}

# Should be set to True in production and False in all other dev and test environments
# Replace with BLOCK_HTTP_REDIRECT_URIS per CBBP-845 to support mobile apps
# REQUIRE_HTTPS_REDIRECT_URIS = True
BLOCK_HTTP_REDIRECT_URIS = False
