from .base import *

# removing security enforcement in development mode
DEBUG = True
SLS_VERIFY_SSL = env('DJANGO_SLS_VERIFY_SSL', False)
SECRET_KEY = env('DJANGO_SECRET_KEY', '1234567890')

HOSTNAME_URL = env('HOSTNAME_URL', 'http://127.0.0.1:8000')

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

# Should be set to True in production and False in all other dev and test environments
# Replace with BLOCK_HTTP_REDIRECT_URIS per CBBP-845 to support mobile apps
# REQUIRE_HTTPS_REDIRECT_URIS = True
BLOCK_HTTP_REDIRECT_URIS = False

APPLICATION_TITLE = "Blue Button 2.0 DEV"
