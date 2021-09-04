from .dev import *

# Override audit logging handler with a file handler
logging_handlers = LOGGING['handlers']

logfile_path = os.path.abspath(os.getcwd() + "/docker-compose/tmp/bb2_logging_test.log")
logdir_path = os.path.abspath(os.getcwd() + "/docker-compose/tmp/")

try:
    # remove left over just in case
    os.remove(logfile_path)
except FileNotFoundError as err:
    print("Error removing left over log file: {}".format(err))

try:
    os.mkdir(logdir_path)
except FileExistsError as err:
    print("Error os.mkdir: {}".format(err))

if logging_handlers is None:
    raise ValueError("Bad settings, expecting handlers defined in settings.LOGGING")

logging_handlers['file'] = {'class': 'logging.FileHandler',
                            'filename': logfile_path, }

loggers = LOGGING.get('loggers')

if loggers:
    logging_logger_audit_handlers = LOGGING['loggers']['audit']['handlers']

    if logging_logger_audit_handlers is None:
        raise ValueError("Bad settings, expecting handlers defined in settings.LOGGING for 'audit' logger")

    logging_logger_audit_handlers.append('file')
