import os
from .base import *

# 20251029 NOTE: Setting this to `False` may disable all
# CSS styling in the application when working locally.
# See:
# * https://stackoverflow.com/questions/5836674/why-does-debug-false-setting-make-my-django-static-files-access-fail
# * https://forum.djangoproject.com/t/django-static-files-in-deployment-debug-false/16675
DEBUG = True
SECRET_KEY = env('DJANGO_SECRET_KEY', default='1234567890')

HOSTNAME_URL = env('HOSTNAME_URL', default='http://localhost:8000')

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
                'hhs_oauth_server.settings.context_processors.export_settings',
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
