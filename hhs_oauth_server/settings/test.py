from .dev import *

from ..utils import is_python2

# Set Python2 to use for unicode field conversion to text
RUNNING_PYTHON2 = is_python2()

del LOGGING['loggers']
# SMS
SEND_SMS = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
REQUIRE_AUTHOIRZE_APP_FLAG = False
LOGIN_RATE = '5000/m'

# Use to skip LDAP tests
AUTH_LDAP_ACTIVE = False

FHIR_CLIENT_CERTSTORE = '/Users/mark/PycharmProjects/hhs_oserver/hhs_oauth_server/hhs_oauth_server/../../certstore'

FHIR_SERVER_DEFAULT = 1

FHIR_SERVER_CONF = {
    'SERVER': 'http://localhost:8000/',
    'PATH': 'fhir-p/',
    'RELEASE': 'baseDstu3/',
    # REWRITE_FROM should be defined as a list
    'REWRITE_FROM': ['http://www.replace.com:8080/baseDstu2',
                     'http://replace.com/baseDstu2'],
    'REWRITE_TO': 'http://localhost:8000/bluebutton/fhir/v1',
}

# url parameters we don't want to pass through to the back-end server
FRONT_END_STRIP_PARAMS = ['access_token',
                          'state',
                          'response_type',
                          'client_id']

REQUEST_CALL_TIMEOUT = (5, 120)
