from .dev import *

del LOGGING['loggers']
# SMS
SEND_SMS = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
REQUIRE_AUTHOIRZE_APP_FLAG = False
LOGIN_RATE = '5000/m'

# Use to skip LDAP tests
AUTH_LDAP_ACTIVE = False
