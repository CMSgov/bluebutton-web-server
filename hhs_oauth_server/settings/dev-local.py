from .base import *
from ..utils import is_python2

# Set Python2 to use for unicode field conversion to text
RUNNING_PYTHON2 = is_python2()

# removing security enforcement in development mode
DEBUG = True
SECRET_KEY = env('DJANGO_SECRET_KEY', '1234567890')

print("BASE: %s" % BASE_DIR)

# database configuration
if os.environ.get('DATABASES_CUSTOM'):
    DATABASES_DEFAULT = os.environ.get('DATABASES_CUSTOM')
else:
    DATABASES_DEFAULT = 'sqlite:///{}/db.sqlite3'.format(BASE_DIR)

DATABASES = {
    'default': dj_database_url.config(default=DATABASES_DEFAULT),
}

print("Databases: %s" % DATABASES)

# Style and UI skins is set here. The default is 'the_skin'
# ENGINE_SKIN = 'the_skin/'
# ENGINE_SKIN = 'usds/'
ENGINE_SKIN = 'cms/'
# An empty ENGINE_SKIN value uses templates from th base templates directory
# ENGINE_SKIN = ""

# adding ability to change authorize form and text in DOT authorize.html
if ENGINE_SKIN == 'cms/':
    # Medicare uses the Medicare form
    OAUTH2_AUTHORIZATION_FORM = 'authorize/medicare.html'
else:
    OAUTH2_AUTHORIZATION_FORM = 'authorize/default.html'

print("skin: %s" % ENGINE_SKIN)

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
        'DIRS': [os.path.join(BASE_DIR, ('templates/' + ENGINE_SKIN))],
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
                'apps.home.templatetags.engine_skin',
            ],
        },
    },
]

HOSTNAME_URL = env('HOSTNAME_URL', 'http://127.0.0.1:8000')
INVITE_REQUEST_ADMIN = env('DJANGO_INVITE_REQUEST_ADMIN', 'sales@videntity.com')

# Stub for Custom Authentication Backend
SLS_USER = env('DJANGO_SLS_USER', 'ben')
SLS_PASSWORD = env('DJANGO_SLS_PASSWORD', 'pbkdf2_sha256$24000$V6XjGqYYNGY7$13tFC13aaTohxBgP2W3glTBz6PSbQN4l6HmUtxQrUys=')
SLS_FIRST_NAME = env('DJANGO_SLS_FIRST_NAME', 'Ben')
SLS_LAST_NAME = env('DJANGO_SLS_LAST_NAME', 'Barker')
SLS_EMAIL = env('DJANGO_SLS_EMAIL', 'ben@example.com')

FHIR_SERVER_DEFAULT = env('DJANGO_FHIRSERVER_ID', 1)

# overrides FHIR server configuration with fake values
FHIR_SERVER_CONF = {
    'SERVER': env('THS_FHIR_SERVER', 'http://fhir.bbonfhir.com/'),
    'PATH': env('THS_FHIR_PATH', 'fhir-p/'),
    'RELEASE': env('THS_FHIR_RELEASE', 'baseDstu2/'),
    # REWRITE_FROM should be defined as a list
    'REWRITE_FROM': env('THS_FHIR_REWRITE_FROM', ['https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3', ]),
    'REWRITE_TO': env('THS_FHIR_REWRITE_TO', 'http://localhost:8000/bluebutton/fhir/v1'),
}

# url parameters we don't want to pass through to the back-end server
FRONT_END_STRIP_PARAMS = ['access_token',
                          'state',
                          'response_type',
                          'client_id']
