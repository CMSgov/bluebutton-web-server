from .dev import *

# Use env-specific logging config if present
# Add file handler.
LOGGING['handlers']['file'] = {
    'class': 'logging.FileHandler',
    'filename': '/code/docker-compose/tmp/bb2_logging_test.log',
}

loggers = LOGGING.get('loggers')

if loggers:
    # Update hhs_server logger
    loggers['hhs_server'] = {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    }
    # Update audit logger
    loggers['audit'] = {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    }
