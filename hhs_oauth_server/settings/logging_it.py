from .dev import *

# Override audit logging handler with a file handler
logging_handlers = LOGGING['handlers']

if logging_handlers is None:
    raise ValueError("Bad settings, expecting handlers defined in settings.LOGGING")

logging_handlers['file'] = {'class': 'logging.FileHandler',
                            'filename': '/code/docker-compose/tmp/bb2_logging_test.log', }

loggers = LOGGING.get('loggers')

if loggers:
    logging_logger_audit_handlers = LOGGING['loggers']['audit']['handlers']

    if logging_logger_audit_handlers is None:
        raise ValueError("Bad settings, expecting handlers defined in settings.LOGGING for 'audit' logger")

    logging_logger_audit_handlers.append('file')
