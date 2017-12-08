from .base import *

# removing security enforcement in development mode
DEBUG = True
SECRET_KEY = env('DJANGO_SECRET_KEY', '1234567890')

HOSTNAME_URL = env('HOSTNAME_URL', 'http://127.0.0.1:8000')
INVITE_REQUEST_ADMIN = env(
    'DJANGO_INVITE_REQUEST_ADMIN', 'change-me@example.com')

TEST_SPECIFIC_APPS = [
    # Installation/Site Specific apps based on  -----------------
    # 'storages',
    # A test client - moved to aws-test / dev /impl settings
    'apps.testclient',

]
INSTALLED_APPS += TEST_SPECIFIC_APPS

# Optional Apps will be loaded by environment.
# We need to be able to check in the urls.py and in html so that we only call
# active reverse matches.
# Therefore add name of optional apps here.
# then add to this list in the settings file for the environment.
# every optional app should have their name added to this list
# Then this variable will be added to SETTINGS_EXPORT below
# so we can test in html templates
OPTIONAL_INSTALLED_APPS += ["testclient", ]

# Skin settings
ENGINE_SKIN = 'the_skin/'

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
