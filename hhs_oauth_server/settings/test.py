from .dev import *

# # Add testac to Test environments only
# if 'apps.fhir.testac' not in INSTALLED_APPS:
#     INSTALLED_APPS = INSTALLED_APPS + [
#         'apps.fhir.testac',
#     ]

# disabling loggers
del LOGGING['loggers']
# SMS
SEND_SMS = False
