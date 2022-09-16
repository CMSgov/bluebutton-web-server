import logging
import json

from django.conf import settings
from apps.dot_ext.loggers import get_session_auth_flow_trace

CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
ERROR = logging.ERROR
WARNING = logging.WARNING
WARN = logging.WARN
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET

AUDIT_BASIC_LOGGER = "audit.basic_logger"
AUDIT_AUTHZ_TOKEN_LOGGER = "audit.authorization.token"
AUDIT_AUTHZ_SLS_LOGGER = "audit.authorization.sls"
AUDIT_DATA_FHIR_LOGGER = "audit.data.fhir"
AUDIT_AUTHN_SLS_LOGGER = "audit.authenticate.sls"
AUDIT_AUTHN_MED_CALLBACK_LOGGER = "audit.authenticate.mymedicare_cb"
AUDIT_AUTHN_MATCH_FHIR_ID_LOGGER = "audit.authenticate.match_fhir_id"
AUDIT_HHS_AUTH_SERVER_REQ_LOGGER = "audit.hhs_oauth_server.request_logging"
AUDIT_GLOBAL_STATE_METRICS_LOGGER = "audit.global_state_metrics"
AUDIT_REQUEST_LOGGER = "audit.request_logger"
AUDIT_WAFFLE_EVENT_LOGGER = "audit.waffle.event"
AUDIT_AUTHFLOW_ID_CLEANUP_LOGGER = "audit.authflow.uuid.cleanup"
AUDIT_CREDS_REQUEST_LOGGER = "audit.creds.request"
PERFORMANCE_LOGGER = 'performance'

LOGGER_NAMES = [
    AUDIT_BASIC_LOGGER,
    AUDIT_AUTHZ_TOKEN_LOGGER,
    AUDIT_AUTHZ_SLS_LOGGER,
    AUDIT_DATA_FHIR_LOGGER,
    AUDIT_AUTHN_SLS_LOGGER,
    AUDIT_AUTHN_MED_CALLBACK_LOGGER,
    AUDIT_AUTHN_MATCH_FHIR_ID_LOGGER,
    AUDIT_HHS_AUTH_SERVER_REQ_LOGGER,
    AUDIT_GLOBAL_STATE_METRICS_LOGGER,
    AUDIT_REQUEST_LOGGER,
    AUDIT_WAFFLE_EVENT_LOGGER,
    AUDIT_AUTHFLOW_ID_CLEANUP_LOGGER
]

HHS_SERVER_LOGNAME_FMT = "hhs_server.{}"


def getLogger(name=None, request=None):
    return RequestLogger(request, name) if request else BasicLogger(name)


class StreamHandler(logging.StreamHandler):
    # a trivial wrapper
    pass


class BasicLogger:
    def __init__(self, logger_name=AUDIT_BASIC_LOGGER):
        self._logger = logging.getLogger(logger_name)

    def logger(self):
        return self._logger

    def format_for_output(self, data_dict, cls=None):
        try:
            if settings.LOG_JSON_FORMAT_PRETTY:
                args = {"sort_keys": True, "indent": 2, "cls": cls}
            else:
                args = {"cls": cls}
            return json.dumps(data_dict, **args)
        except Exception:
            return "Could not turn the data_dict into a JSON dump"

    def debug(self, data_dict, cls=None):
        self._logger.debug(self.format_for_output(data_dict, cls=cls))

    def info(self, data_dict, cls=None):
        self._logger.info(self.format_for_output(data_dict, cls=cls))

    def error(self, data_dict, cls=None):
        self._logger.error(self.format_for_output(data_dict, cls=cls))

    def warning(self, data_dict, cls=None):
        self._logger.warning(self.format_for_output(data_dict, cls=cls))

    def critical(self, data_dict, cls=None):
        self._logger.critical(self.format_for_output(data_dict, cls=cls))

    def exception(self, data_dict, cls=None):
        self._logger.exception(self.format_for_output(data_dict, cls=cls))

    def setLevel(self, lvl):
        self._logger.setLevel(lvl)


class RequestLogger(BasicLogger):
    def __init__(self, request, logger_name=AUDIT_REQUEST_LOGGER):
        super().__init__(logger_name=logger_name)
        self.standard_log_data = {}
        if request:
            self.extract_request_data(request)

    def extract_request_data(self, request):
        try:
            self.standard_log_data["request_uuid"] = request._logging_uuid
        except Exception:
            self.standard_log_data["request_uuid"] = None
        try:
            self.standard_log_data["auth_uuid"] = request.session["auth_uuid"]
        except Exception:
            self.standard_log_data["auth_uuid"] = None
        try:
            self.standard_log_data["auth_app_id"] = request.session["auth_app_id"]
        except Exception:
            self.standard_log_data["auth_app_id"] = None
        try:
            self.standard_log_data["auth_app_name"] = request.session["auth_app_name"]
        except Exception:
            self.standard_log_data["auth_app_name"] = None
        try:
            self.standard_log_data["auth_client_id"] = request.session["auth_client_id"]
        except Exception:
            self.standard_log_data["auth_client_id"] = None
        try:
            self.standard_log_data["auth_pkce_method"] = request.session["auth_pkce_method"]
        except Exception:
            self.standard_log_data["auth_pkce_method"] = None

        self.standard_log_data.update(get_session_auth_flow_trace(request))

    def format_for_output(self, data_dict, cls=None):
        merged_dict = {**self.standard_log_data, **data_dict}
        return super().format_for_output(merged_dict, cls=cls)

    def debug(self, data_dict, request=None, cls=None):
        self._logger.debug(self.format_for_output(data_dict, cls=cls))

    def info(self, data_dict, request=None, cls=None):
        self._logger.info(self.format_for_output(data_dict, cls=cls))

    def error(self, data_dict, request=None, cls=None):
        self._logger.error(self.format_for_output(data_dict, cls=cls))

    def warning(self, data_dict, cls=None):
        self._logger.warning(self.format_for_output(data_dict, cls=cls))

    def critical(self, data_dict, cls=None):
        self._logger.critical(self.format_for_output(data_dict, cls=cls))

    def exception(self, data_dict, cls=None):
        self._logger.exception(self.format_for_output(data_dict, cls=cls))
