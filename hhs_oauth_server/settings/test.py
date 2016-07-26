from .dev import *

# Add testac to Test environments only
INSTALLED_APPS = INSTALLED_APPS + [
    'apps.fhir.testac',
]

# disabling loggers
del LOGGING['loggers']
