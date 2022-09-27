import io

import apps.logging.request_logger as logging

"""
  Utility functions for logging, and logging manipulations (used in tests)
"""


def format_timestamp(dt):
    """
    Returns an ISO 6801 format string in UTC that works well with AWS Glue/Athena
    """
    return (
        dt.replace(microsecond=0).isoformat().replace("+00:00", "")
        if dt is not None
        else None
    )


def redirect_loggers_custom(custom_loggers):
    return _redirect_loggers(custom_loggers)


def redirect_loggers():
    return _redirect_loggers(logging.LOGGER_NAMES)


def _redirect_loggers(logger_names):
    logger_registry = {}
    for n in logger_names:
        logger = logging.getLogger(n)
        log_buffer = io.StringIO()
        log_channel = logging.StreamHandler(log_buffer)
        log_channel.setLevel(logging.INFO)
        logger.logger().setLevel(logging.INFO)
        logger.logger().addHandler(log_channel)
        logger_registry[n] = (log_buffer, log_channel)
    return logger_registry


def cleanup_logger(logger_registry: dict):
    # do not close stream, only close channel
    for k, v in logger_registry.items():
        v[1].close()
    logger_registry.clear()


def get_log_lines_list(logger_registry: dict, logger_name: str):
    buf = io.StringIO(get_log_content(logger_registry, logger_name))
    lines = buf.readlines()
    return lines


def get_log_content(logger_registry: dict, logger_name: str, override_loggers=[]):
    if override_loggers:
        return collect_logs(logger_registry, override_loggers).get(logger_name)
    else:
        return collect_logs(logger_registry).get(logger_name)


def collect_logs(logger_registry: dict, override_loggers=[]):
    log_contents = {}
    logger_names = logging.LOGGER_NAMES if not override_loggers else override_loggers
    for n in logger_names:
        v = logger_registry.get(n)
        log_contents[n] = v[0].getvalue()
    return log_contents
