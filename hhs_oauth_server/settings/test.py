from .dev import *

del LOGGING['loggers']
# SMS
SEND_SMS = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
