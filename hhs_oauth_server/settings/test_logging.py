from .dev import *

# Use env-specific logging config if present
# Add file handler.
LOGGING['handlers']['file'] = {
    'class': 'logging.FileHandler',
    'filename': '/code/docker-compose/tmp/bb2_logging_test.log',
}

if LOGGING.get('loggers'):
    # Update hhs_server logger
    LOGGING.get['loggers']['hhs_server'] = {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    }
    # Update audit logger
    LOGGING['loggers']['audit'] = {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    }
