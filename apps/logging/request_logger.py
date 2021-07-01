import logging
import json

from django.conf import settings
from apps.dot_ext.loggers import get_session_auth_flow_trace


class BasicLogger:
    def __init__(self, logger_name="basic_logger"):
        self._logger = logging.getLogger(logger_name)

    def format_for_output(self, data_dict):
        try:
            if settings.LOG_JSON_FORMAT_PRETTY:
                return json.dumps(data_dict, indent=2)
            else:
                return json.dumps(data_dict)
        except Exception:
            return "Could not turn the data_dict into a JSON dump"

    def debug(self, data_dict):
        self._logger.debug(self.format_for_output(data_dict))

    def info(self, data_dict):
        self._logger.info(self.format_for_output(data_dict))

    def error(self, data_dict):
        self._logger.error(self.format_for_output(data_dict))


class RequestLogger(BasicLogger):
    def __init__(self, request):
        super().__init__(logger_name="request_logger")
        self.standard_log_data = {}
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

    def format_for_output(self, data_dict):
        merged_dict = {**self.standard_log_data, **data_dict}
        return super().format_for_output(merged_dict)

    def debug(self, data_dict):
        self._logger.debug(self.format_for_output(data_dict))

    def info(self, data_dict):
        self._logger.info(self.format_for_output(data_dict))

    def error(self, data_dict):
        self._logger.error(self.format_for_output(data_dict))
