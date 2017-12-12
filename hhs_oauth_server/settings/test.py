from .dev import *

del LOGGING['loggers']

SEND_SMS = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
REQUIRE_AUTHOIRZE_APP_FLAG = False
LOGIN_RATE = '5000/m'

FHIR_SERVER_DEFAULT = 1

REQUEST_CALL_TIMEOUT = (5, 120)

# fix duplicate load. Already loaded in dev.py per style used for aws-*.py
# INSTALLED_APPS.append('apps.testclient')

OFFLINE = True
