from .dev import *

del LOGGING['loggers']

SEND_SMS = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
REQUIRE_AUTHOIRZE_APP_FLAG = False
AXES_COOLOFF_TIME = datetime.timedelta(seconds=60)
AXES_FAILURE_LIMIT = 100
LOGIN_RATE = '100/m'
FHIR_SERVER_DEFAULT = 1

REQUEST_CALL_TIMEOUT = (5, 120)

OFFLINE = True
# Should be set to True in production and False in all other dev and test environments
REQUIRE_HTTPS_REDIRECT_URIS = False
