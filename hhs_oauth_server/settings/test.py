from .dev import *

del LOGGING['loggers']

SEND_SMS = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
REQUIRE_AUTHOIRZE_APP_FLAG = False
LOGIN_RATE = '5000/m'

FHIR_SERVER_DEFAULT = 1

REQUEST_CALL_TIMEOUT = (5, 120)

OFFLINE = True
