import logging
import json

from django.conf import settings
from apps.dot_ext.loggers import get_session_auth_flow_trace


def getLogger(name=None):
    return RequestLogger(None, name) if name else BasicLogger()


class BasicLogger:
    def __init__(self, logger_name="audit.basic_logger"):
        self._logger = logging.getLogger(logger_name)

    def logger(self):
        return self._logger

    def format_for_output(self, data_dict, cls=None):
        # expect data_dict as a dict, or a class that has to_dict() implemented
        tmp_dict = data_dict if isinstance(data_dict, dict) else data_dict.to_dict()
        try:
            return json.dumps(tmp_dict, indent=2 if settings.LOG_JSON_FORMAT_PRETTY else None, cls=cls)
        except Exception:
            return "Could not turn the data_dict into a JSON dump"

    def debug(self, data_dict, cls=None):
        self._logger.debug(data_dict if isinstance(data_dict, str) else self.format_for_output(data_dict, cls=cls))

    def info(self, data_dict, cls=None):
        self._logger.info(data_dict if isinstance(data_dict, str) else self.format_for_output(data_dict, cls=cls))

    def error(self, data_dict, cls=None):
        self._logger.error(data_dict if isinstance(data_dict, str) else self.format_for_output(data_dict, cls=cls))


class RequestLogger(BasicLogger):
    def __init__(self, request, logger_name="audit.request_logger"):
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
        self.standard_log_data.update(get_session_auth_flow_trace(request))

    def format_for_output(self, data_dict, cls=None):
        tmp_dict = data_dict if isinstance(data_dict, dict) else data_dict.to_dict()
        merged_dict = {**self.standard_log_data, **tmp_dict}
        return super().format_for_output(merged_dict, cls=cls)

    def debug(self, data_dict, request=None, cls=None):
        self._logger.debug(data_dict if isinstance(data_dict, str) else self.format_for_output(data_dict, cls=cls))

    def info(self, data_dict, request=None, cls=None):
        self._logger.info(data_dict if isinstance(data_dict, str) else self.format_for_output(data_dict, cls=cls))

    def error(self, data_dict, request=None, cls=None):
        self._logger.error(data_dict if isinstance(data_dict, str) else self.format_for_output(data_dict, cls=cls))
