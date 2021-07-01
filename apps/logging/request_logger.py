import logging
import json

from django.conf import settings
from apps.dot_ext.loggers import get_session_auth_flow_trace


class RequestLogger:
    def __init__(self, request):
        self.standard_log_data = {}
        self.extract_request_data(request)
        self._logger = logging.getLogger("request_logger")

    def extract_request_data(self, request):
        self.standard_log_data["request_uuid"] = request._logging_uuid
        self.standard_log_data["auth_uuid"] = request.session["auth_uuid"]
        self.standard_log_data.update(get_session_auth_flow_trace(request))

    def format_for_output(self, data_dict):
        merged_dict = {**self.standard_log_data, **data_dict}

        if settings.LOG_JSON_FORMAT_PRETTY:
            return json.dumps(merged_dict, indent=2)
        else:
            return json.dumps(merged_dict)

    def debug(self, data_dict):
        self._logger.debug(self.format_for_output(data_dict))

    def info(self, data_dict):
        self._logger.info(self.format_for_output(data_dict))

    def error(self, data_dict):
        self._logger.error(self.format_for_output(data_dict))


class BasicLogger:
    def __init__(self, request):
        self._logger = logging.getLogger("basic_logger")

    def format_for_output(self, data_dict):
        if settings.LOG_JSON_FORMAT_PRETTY:
            return json.dumps(data_dict, indent=2)
        else:
            return json.dumps(data_dict)

    def debug(self, data_dict):
        self._logger.debug(self.format_for_output(data_dict))

    def info(self, data_dict):
        self._logger.info(self.format_for_output(data_dict))

    def error(self, data_dict):
        self._logger.error(self.format_for_output(data_dict))
