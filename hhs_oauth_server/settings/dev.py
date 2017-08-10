from .base import *
from ..utils import is_python2

# Set Python2 to use for unicode field conversion to text
RUNNING_PYTHON2 = is_python2()

# removing security enforcement in development mode
DEBUG = True
SECRET_KEY = env('DJANGO_SECRET_KEY', '1234567890')

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
    'REWRITE_FROM': env('THS_FHIR_REWRITE_FROM', ['http://ec2-52-4-198-86.compute-1.amazonaws.com:8080/baseDstu2', ]),
    'REWRITE_TO': env('THS_FHIR_REWRITE_TO', 'http://localhost:8000/bluebutton/fhir/v1'),
}

# url parameters we don't want to pass through to the back-end server
FRONT_END_STRIP_PARAMS = ['access_token',
                          'state',
                          'response_type',
                          'client_id']
