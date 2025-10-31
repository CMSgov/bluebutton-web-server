import datetime
import hashlib
import json
import uuid

import apps.logging.request_logger as logging

from django.core.exceptions import ObjectDoesNotExist
from django.utils.deprecation import MiddlewareMixin
from oauth2_provider.models import AccessToken, RefreshToken, get_application_model
from rest_framework.response import Response
from apps.constants import Versions

from apps.dot_ext.loggers import (
    SESSION_AUTH_FLOW_TRACE_KEYS,
    get_session_auth_flow_trace,
    is_path_part_of_auth_flow_trace,
)
from apps.fhir.bluebutton.utils import (
    get_ip_from_request,
    get_user_from_request,
    get_access_token_from_request,
)

audit = logging.getLogger("audit.%s" % __name__)


class RequestResponseLog(object):
    """Audit log message to JSON string

    The JSON log entry contains the following fields when available:
        NOTE: Items are tagged with the Jira ticket number when they were added.
        - access_token_hash = Hash of the access token.
        - access_token_id = AC id. (BB2-342)
        - access_token_scopes =  Access token scopes when available.
        - app_id = Application id.
        - app_name = Application name.
        - app_require_demographic_scopes = Application required scopes choice.
        - auth_app_id = Application id for auth flow session.
        - auth_app_name = Application name for auth flow session.
        - auth_app_data_access_type = data access type of the application: ONE_TIME, THIRTEEN_MONTH, RESEARCH_STUDY (BB2-2011)
        - auth_app_end_date = expiration date of application of type: RESEARCH_STUDY (BB2-2011)
        - auth_client_id = Client ID for auth flow session.
        - auth_require_demographic_scopes = Application required scopes choice.
        - auth_uuid = The UUID identifying the auth flow session.
        - dev_id = Developer user id.
        - dev_name = Developer user name.
        - elapsed = Response time (end_time - start_time)
        - end_time = Unix Epoch format time of the response processed.
        - fhir_attribute_count = FHIR payload number of top level object attributes.
        - fhir_bundle_type = FHIR payload 'type'.
        - fhir_entry_count = FHIR entry count in response.
        - fhir_id = Bene patient id.
        - fhir_resource_id = FHIR payload 'id'.
        - fhir_resource_type = FHIR payload 'resourceType'.
        - ip_addr = IP address of the request, account for the possibility of being behind a proxy.
        - location = Location (redirect) for 300,301,302,307 response codes.
        - path = The request.path.
        - req_access_token_hash = Request AC hash. (BB2-342)
        - req_allow = Request AC allow. (BB2-342)
        - req_app_id = Request AC app id. (BB2-342)
        - req_app_name = Request AC app name. (BB2-342)
        - req_client_id = Request client_id. (BB2-342)
        - req_code_challenge_method = Request code challenge_method. (BB2-342)
        - req_fhir_id = Request FHIR_ID. (BB2-342)
        - req_grant_type = Request grant type. (BB2-342)
        - req_header_accept_encoding = Req header info. (BB2-342)
        - req_header_content_length = Req header info. (BB2-342)
        - req_header_content_type = Req header info. (BB2-342)
        - req_header_host = Req header info. (BB2-342)
        - req_header_referrer = Req header info. (BB2-342)
        - req_header_user_agent = Req header info. (BB2-342)
        - req_post_grant_type = Post grant type. (BB2-342)
        - req_qparam_beneficiary = Info from HTTP Query Params. (BB2-342)
        - req_qparam_beneficiary = Info from HTTP Query Params. (BB2-342)
        - req_qparam_client_id = Info from HTTP Query Params. (BB2-342)
        - req_qparam__count = Info from HTTP Query Params. (BB2-342)
        - req_qparam_count = Info from HTTP Query Params. (BB2-342)
        - req_qparam_format = Info from HTTP Query Params. (BB2-342)
        - req_qparam__id = Info from HTTP Query Params. (BB2-342)
        - req_qparam_lastupdated = Info from HTTP Query Params. (BB2-342)
        - req_qparam_patient = Info from HTTP Query Params. (BB2-342)
        - req_qparam_response_type = Info from HTTP Query Params. (BB2-342)
        - req_qparam_startindex = Info from HTTP Query Params. (BB2-342)
        - req_qparam_type = Info from HTTP Query Params. (BB2-342)
        - req_redirect_uri = Request redirect URI. (BB2-342)
        - req_refresh_token_hash = Request refresh token hash. (BB2-342)
        - req_response_type = Response type. (BB2-342)
        - req_scope = Request scope (BB2-342)
        - req_share_demographic_scopes = Request bene share demo scopes. (BB2-342)
        - request_method = http request method type (GET/POST/etc) (BB2-342)
        - request_scheme = The scheme of the request (http/https/etc) (BB2-342)
        - request_uuid = The UUID identifying the request.
        - req_user_id = Request user id. (BB2-342)
        - req_user_username = Request username. (BB2-342)
        - resp_access_token_hash = Response AC info. (BB2-342)
        - resp_access_token_scopes = Response AC info. (BB2-342)
        - resp_app_id = Response AC info. (BB2-342)
        - resp_app_name = Response AC info. (BB2-342)
        - resp_app_require_demographic_scopes = Response AC info. (BB2-342)
        - resp_dev_id = Response AC info. (BB2-342)
        - resp_dev_name = Response AC info. (BB2-342)
        - resp_expires_in = Response AC info. (BB2-342)
        - resp_fhir_id = Response AC info. (BB2-342)
        - response_code = The response status code.
        - resp_refresh_token_hash = Response refresh token info. (BB2-342)
        - resp_scope = Response refresh token info. (BB2-342)
        - resp_token_type = Response refresh token info. (BB2-342)
        - resp_user_id = Response refresh token info. (BB2-342)
        - resp_user_username = Response refresh token info. (BB2-342)
        - size = Size in bytes of the response.content
        - start_time = Unix Epoch format time of the request processed.
        - type = Label for type of log. Set to "request_response_middleware". (BB2-342)
        - user_id = Login user (or None) or OAuth2 API id. (BB2-342)
        - user = Login user (or None) or OAuth2 API username.
        - user_username = Login user (or None) or OAuth2 API username. (BB2-342)
        - data_facilitator_end_user = End user for data facilitator app. (BB2-3345)
    """

    request = None
    response = None

    def __init__(self, req, resp):
        self.request = req
        self.response = resp
        """
        Init log message. NOTE: These values set to empty for backward Splunk dashboard compatibility.
        The convention for newly added items is to set empty values to None.
        """
        self.log_msg = {}
        self.log_msg["type"] = "request_response_middleware"
        self.log_msg["access_token_hash"] = ""
        self.log_msg["app_id"] = ""
        self.log_msg["app_name"] = ""
        self.log_msg["dev_id"] = ""
        self.log_msg["dev_name"] = ""
        self.log_msg["location"] = ""
        self.log_msg["size"] = 0

    def _log_msg_update_from_dict(self, from_dict, key, dict_key):
        # Log message update from a passed in dictionary
        try:
            value = from_dict.get(dict_key, None)
            if value is not None:
                if len(str(value)) > 0:
                    self.log_msg[key] = value
        except ObjectDoesNotExist:
            self.log_msg[key] = (
                "ObjectDoesNotExist exception for key " + key + ":" + dict_key
            )
        except AttributeError:
            self.log_msg[key] = (
                "AttributeError exception for key " + key + ":" + dict_key
            )

    def _log_msg_update_from_object(self, obj, key, obj_key):
        # Log message update from a passed in object
        try:
            value = getattr(obj, obj_key, None)
            # Added as the fhir_id column on crosswalk is now a method rather than a property
            if callable(value):
                value = value()
            if value is not None:
                if len(str(value)) > 0:
                    self.log_msg[key] = value
        except ObjectDoesNotExist:
            self.log_msg[key] = (
                "ObjectDoesNotExist exception for key " + key + ":" + obj_key
            )
        except AttributeError:
            self.log_msg[key] = (
                "AttributeError exception for key " + key + ":" + obj_key
            )

    def _log_msg_update_from_querydict(self, key, qp_key):
        # Log message update from request QueryDict HTTP query parameters
        try:
            value_list = self.request.GET.getlist(qp_key, None)
            if value_list is not None:
                if len(value_list) == 1:
                    self.log_msg[key] = value_list[0]
                elif len(value_list) > 1:
                    self.log_msg[key] = value_list
        except ObjectDoesNotExist:
            self.log_msg[key] = (
                "ObjectDoesNotExist exception for key " + key + ":" + qp_key
            )
        except AttributeError:
            self.log_msg[key] = "AttributeError exception for key " + key + ":" + qp_key

    def _sync_app_name(self):
        if self.log_msg.get("app_id") is not None and self.log_msg.get("app_name") is not None \
           and not self.log_msg.get("app_id") and not self.log_msg.get("app_name") \
           and self.log_msg.get("auth_app_id") and self.log_msg.get("auth_app_name"):
            self.log_msg["app_id"] = self.log_msg["auth_app_id"]
            self.log_msg["app_name"] = self.log_msg["auth_app_name"]

    def to_dict(self):
        """
        --- Logging custom items ---
        """
        self.log_msg["start_time"] = self.request._logging_start_dt.timestamp()
        self.log_msg["end_time"] = datetime.datetime.utcnow().timestamp()
        self.log_msg["elapsed"] = (
            datetime.datetime.utcnow().timestamp()
            - self.request._logging_start_dt.timestamp()
        )
        self.log_msg["ip_addr"] = get_ip_from_request(self.request)
        self.log_msg["request_uuid"] = str(self.request._logging_uuid)

        """
        --- Logging items from request.POST ---
        """
        if getattr(self.request, "POST", False):
            self._log_msg_update_from_dict(
                self.request.POST, "req_post_grant_type", "grant_type"
            )

        """
        --- Logging items from request.headers ---
        """
        if getattr(self.request, "headers", False):
            request_headers = getattr(self.request, "headers")
            self._log_msg_update_from_dict(
                request_headers, "req_header_accept_encoding", "Accept-Encoding"
            )
            self._log_msg_update_from_dict(
                request_headers, "req_header_content_length", "Content-Length"
            )
            self._log_msg_update_from_dict(
                request_headers, "req_header_content_type", "Content-Type"
            )
            self._log_msg_update_from_dict(request_headers, "req_header_host", "Host")
            self._log_msg_update_from_dict(
                request_headers, "req_header_referrer", "Referer"
            )
            self._log_msg_update_from_dict(
                request_headers, "req_header_user_agent", "User-Agent"
            )
            self._log_msg_update_from_dict(
                request_headers, "req_header_bluebutton_sdk", "X-BLUEBUTTON-SDK"
            )
            self._log_msg_update_from_dict(
                request_headers, "req_header_bluebutton_sdk_version", "X-BLUEBUTTON-SDK-VERSION"
            )
            self._log_msg_update_from_dict(
                request_headers, "req_header_bluebutton_app", "X-BLUEBUTTON-APP"
            )
            self._log_msg_update_from_dict(
                request_headers, "req_header_bluebutton_app_version", "X-BLUEBUTTON-APP-VERSION"
            )
            self._log_msg_update_from_dict(
                request_headers, "data_facilitator_end_user", "DATA-END-USER"
            )

        """
        --- Logging items from request.body ---
        """
        if getattr(self.request, "body", False):
            req_body = self.request.body.decode("utf-8", "ignore")
            try:
                request_body_dict = dict(
                    item.split("=") for item in req_body.split("&")
                )
                self._log_msg_update_from_dict(
                    request_body_dict, "req_client_id", "client_id"
                )

                if self.log_msg.get("req_client_id", False):
                    try:
                        application = get_application_model().objects.get(
                            client_id=self.log_msg.get("req_client_id")
                        )
                        self._log_msg_update_from_object(application, "req_app_name", "name")
                        self._log_msg_update_from_object(application, "req_app_id", "id")
                    except ObjectDoesNotExist:
                        self.log_msg["req_app_name"] = ""
                        self.log_msg["req_app_id"] = ""

                refresh_token = request_body_dict.get("refresh_token", None)
                if refresh_token is not None:
                    self.log_msg["req_refresh_token_hash"] = hashlib.sha256(
                        str(refresh_token).encode("utf-8")
                    ).hexdigest()

                # Log AC passed from RequestTimeLoggingMiddleware.process_request() pre-response
                self._log_msg_update_from_object(
                    self.request, "req_access_token_hash", "_req_access_token_hash"
                )

                self._log_msg_update_from_dict(
                    request_body_dict, "req_response_type", "response_type"
                )
                self._log_msg_update_from_dict(
                    request_body_dict,
                    "req_code_challenge_method",
                    "code_challenge_method",
                )
                self._log_msg_update_from_dict(
                    request_body_dict, "req_grant_type", "grant_type"
                )
                self._log_msg_update_from_dict(
                    request_body_dict, "req_redirect_uri", "redirect_uri"
                )
                self._log_msg_update_from_dict(request_body_dict, "req_scope", "scope")
                self._log_msg_update_from_dict(
                    request_body_dict,
                    "req_share_demographic_scopes",
                    "share_demographic_scopes",
                )
                self._log_msg_update_from_dict(request_body_dict, "req_allow", "allow")
            except ObjectDoesNotExist:
                pass
            except ValueError:
                pass

        """
        --- Logging items from request.user ---
        """
        if getattr(self.request, "user", False):
            self._log_msg_update_from_object(self.request.user, "req_user_id", "id")
            self._log_msg_update_from_object(
                self.request.user, "req_user_username", "username"
            )
            if getattr(self.request.user, "crosswalk", False):
                self._log_msg_update_from_object(
                    self.request.user.crosswalk, "req_fhir_id", "fhir_id"
                )

        """
        --- Logging items from request.session for Auth Flow Tracing ---
        """
        if getattr(self.request, "session", False) and is_path_part_of_auth_flow_trace(self.request.path):
            auth_flow_dict = get_session_auth_flow_trace(self.request)
            for k in SESSION_AUTH_FLOW_TRACE_KEYS:
                if auth_flow_dict.get(k, None):
                    self.log_msg[k] = auth_flow_dict.get(k, None)

        """
        --- Logging items from request.GET for query params ---
        """
        if getattr(self.request, "GET", False):
            # Log selected query params only
            self._log_msg_update_from_querydict("req_qparam__count", "_count")
            self._log_msg_update_from_querydict("req_qparam__id", "_id")
            self._log_msg_update_from_querydict("req_qparam_beneficiary", "beneficiary")
            self._log_msg_update_from_querydict("req_qparam_beneficiary", "Beneficiary")
            self._log_msg_update_from_querydict("req_qparam_client_id", "client_id")
            self._log_msg_update_from_querydict("req_qparam_lang", "lang")
            self._log_msg_update_from_querydict("req_qparam_count", "count")
            self._log_msg_update_from_querydict("req_qparam_format", "_format")
            self._log_msg_update_from_querydict(
                "req_qparam_lastupdated", "_lastUpdated"
            )

            self._log_msg_update_from_querydict("req_qparam_patient", "patient")
            self._log_msg_update_from_querydict("req_qparam_patient", "Patient")
            self._log_msg_update_from_querydict(
                "req_qparam_response_type", "response_type"
            )

            self._log_msg_update_from_querydict("req_qparam_startindex", "startIndex")
            self._log_msg_update_from_querydict("req_qparam_type", "type")

            if self.log_msg.get("req_qparam_client_id", False):
                try:
                    application = get_application_model().objects.get(
                        client_id=self.log_msg.get("req_qparam_client_id")
                    )
                    self._log_msg_update_from_object(application, "req_app_name", "name")
                    self._log_msg_update_from_object(application, "req_app_id", "id")
                except ObjectDoesNotExist:
                    self.log_msg["req_app_name"] = ""
                    self.log_msg["req_app_id"] = ""

        """
        --- Logging items from request ---
        """
        self._log_msg_update_from_object(self.request, "path", "path")
        self._log_msg_update_from_object(self.request, "request_method", "method")
        self._log_msg_update_from_object(self.request, "request_scheme", "scheme")

        """
        --- Logging items from get_user_from_request() ---
        """
        user = get_user_from_request(self.request)
        if user:
            self.log_msg["user"] = str(user)
            try:
                self.log_msg["fhir_id_v2"] = user.crosswalk.fhir_id(Versions.V2)
                self.log_msg['fhir_id_v3'] = user.crosswalk.fhir_id(Versions.V3)
            except ObjectDoesNotExist:
                pass

        """
        --- Logging items from request access token ---
        """
        access_token = getattr(
            self.request, "auth", get_access_token_from_request(self.request)
        )

        if access_token:
            try:
                at = AccessToken.objects.get(token=access_token)

                self.log_msg["access_token_hash"] = hashlib.sha256(
                    str(access_token).encode("utf-8")
                ).hexdigest()
                self.log_msg["access_token_scopes"] = " ".join([s for s in at.scopes])
                self._log_msg_update_from_object(
                    at, "access_token_id", "id"
                )

                self._log_msg_update_from_object(at.application, "app_name", "name")
                self._log_msg_update_from_object(at.application, "app_id", "id")
                self._log_msg_update_from_object(
                    at.application,
                    "app_require_demographic_scopes",
                    "require_demographic_scopes",
                )
                self._log_msg_update_from_object(at.application.user, "dev_id", "id")
                self._log_msg_update_from_object(
                    at.application.user, "dev_name", "username"
                )

                self._log_msg_update_from_object(at.user, "user_id", "id")
                self._log_msg_update_from_object(at.user, "user_username", "username")
            except ObjectDoesNotExist:
                pass

        """
        --- Logging items from response ---
        """
        self.log_msg["response_code"] = getattr(self.response, "status_code", 0)
        if self.log_msg["response_code"] in (300, 301, 302, 307):
            self.log_msg["location"] = self.response.get("Location", "?")
        elif getattr(self.response, "content", False):
            self.log_msg["size"] = len(self.response.content)

        """
        --- Logging items from a FHIR type response ---
        """
        if isinstance(self.response, Response) and isinstance(self.response.data, dict):
            self.log_msg["fhir_bundle_type"] = self.response.data.get("type", None)
            self.log_msg["fhir_resource_id"] = self.response.data.get("id", None)
            self.log_msg["fhir_resource_type"] = self.response.data.get(
                "resourceType", None
            )
            self.log_msg["fhir_attribute_count"] = len(self.response.data)
            if self.response.data.get("entry", False):
                self.log_msg["fhir_entry_count"] = len(self.response.data.get("entry"))
            else:
                self.log_msg["fhir_entry_count"] = None

        """
        --- Logging items from response content (refresh_token)
        """
        if (
            getattr(self.response, "content", False)
            and self.log_msg.get("req_post_grant_type", False)
            and self.log_msg.get("request_method", False)
        ):

            if (
                self.log_msg["req_post_grant_type"] == "refresh_token"
                and self.log_msg["request_method"] == "POST"
            ):
                try:
                    response_content = json.loads(self.response.content)
                except json.decoder.JSONDecodeError:
                    response_content = {}  # Set to empty DICT

                self._log_msg_update_from_dict(
                    response_content, "resp_fhir_id", "patient"
                )
                self._log_msg_update_from_dict(
                    response_content, "resp_expires_in", "expires_in"
                )
                self._log_msg_update_from_dict(
                    response_content, "resp_token_type", "token_type"
                )
                self._log_msg_update_from_dict(response_content, "resp_scope", "scope")

                self.log_msg["resp_refresh_token_hash"] = hashlib.sha256(
                    str(response_content.get("refresh_token", None)).encode("utf-8")
                ).hexdigest()

                resp_access_token = response_content.get("access_token", None)

                if resp_access_token:
                    try:
                        at = AccessToken.objects.get(token=resp_access_token)

                        self.log_msg["resp_access_token_hash"] = hashlib.sha256(
                            str(at).encode("utf-8")
                        ).hexdigest()

                        self.log_msg["resp_access_token_scopes"] = " ".join(
                            [s for s in at.scopes]
                        )

                        self._log_msg_update_from_object(
                            at.application, "resp_app_id", "id"
                        )
                        self._log_msg_update_from_object(
                            at.application, "resp_app_name", "name"
                        )
                        self._log_msg_update_from_object(
                            at.application,
                            "resp_app_require_demographic_scopes",
                            "require_demographic_scopes",
                        )
                        self._log_msg_update_from_object(
                            at.application.user, "resp_dev_id", "id"
                        )
                        self._log_msg_update_from_object(
                            at.application.user, "resp_dev_name", "username"
                        )

                        self._log_msg_update_from_object(at.user, "resp_user_id", "id")
                        self._log_msg_update_from_object(
                            at.user, "resp_user_username", "username"
                        )
                    except ObjectDoesNotExist:
                        pass
        self._sync_app_name()
        return self.log_msg

##############################################################################
#
# Request time logging middleware
# https://djangosnippets.org/snippets/1826/
#
##############################################################################


class RequestTimeLoggingMiddleware(MiddlewareMixin):
    """Middleware class logging request time to stderr.

    This class can be used to measure time of request processing
    within Django.  It can be also used to log time spent in
    middleware and in view itself, by putting middleware multiple
    times in INSTALLED_MIDDLEWARE.

    Static method `log_message' may be used independently of the
    middleware itself, outside of it, and even when middleware is not
    listed in INSTALLED_MIDDLEWARE.
    """

    @staticmethod
    def log_message(request, response):
        audit.info(RequestResponseLog(request, response).to_dict())
        request._logging_pass += 1

    def process_request(self, request):
        """
        --- Get request (pre-response) logging items
        """
        request._logging_uuid = str(uuid.uuid1())
        request._logging_start_dt = datetime.datetime.utcnow()
        request._logging_pass = 1
        request._logger = audit

        # Get access token to be refreshed pre-response, since it is removed
        if getattr(request, "body", False):
            req_body = request.body.decode("utf-8", "ignore")
            try:
                request_body_dict = dict(
                    item.split("=") for item in req_body.split("&")
                )

                refresh_token = request_body_dict.get("refresh_token", None)
                if refresh_token is not None:
                    rt = RefreshToken.objects.get(token=refresh_token)
                    if rt:
                        request._req_access_token_hash = hashlib.sha256(
                            str(rt.access_token).encode("utf-8")
                        ).hexdigest()
            except ValueError:
                pass
            except ObjectDoesNotExist:
                pass

    def process_response(self, request, response):
        self.log_message(request, response)
        return response
