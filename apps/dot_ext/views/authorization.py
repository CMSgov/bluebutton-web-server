import json
import logging
from datetime import datetime, timedelta
from time import strftime

import waffle
from waffle import get_waffle_flag_model

from django.http.response import HttpResponse, HttpResponseBadRequest
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.views.base import app_authorized, get_access_token_model
from oauth2_provider.views.base import AuthorizationView as DotAuthorizationView
from oauth2_provider.views.base import TokenView as DotTokenView
from oauth2_provider.views.base import RevokeTokenView as DotRevokeTokenView
from oauth2_provider.views.introspect import (
    IntrospectTokenView as DotIntrospectTokenView,
)
from oauth2_provider.models import get_application_model
from oauthlib.oauth2.rfc6749.errors import InvalidClientError, InvalidGrantError
from rest_framework import status
from urllib.parse import urlparse, parse_qs
import html
from apps.dot_ext.scopes import CapabilitiesScopes
import apps.logging.request_logger as bb2logging

from ..signals import beneficiary_authorized_application
from ..forms import SimpleAllowForm
from ..loggers import (
    create_session_auth_flow_trace,
    cleanup_session_auth_flow_trace,
    get_session_auth_flow_trace,
    set_session_auth_flow_trace,
    set_session_auth_flow_trace_value,
    update_instance_auth_flow_trace_with_code,
)
from ..models import Approval
from ..utils import (
    remove_application_user_pair_tokens_data_access,
    validate_app_is_active,
    json_response_from_oauth2_error,
)
from ...authorization.models import DataAccessGrant

log = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

QP_CHECK_LIST = ["client_secret"]


def get_grant_expiration(data_access_type):

    pass


class AuthorizationView(DotAuthorizationView):
    """
    Override the base authorization view from dot to
    use the custom AllowForm.
    """
    application = None
    version = None
    form_class = SimpleAllowForm
    login_url = "/mymedicare/login"

    def __init__(self, version=1):
        self.version = version
        super().__init__()

    def get_context_data(self, **kwargs):
        context = super(AuthorizationView, self).get_context_data(**kwargs)
        context['permission_end_date_text'] = self.application.access_end_date_text()
        context['permission_end_date'] = self.application.access_end_date()
        return context

    def dispatch(self, request, *args, **kwargs):
        """
        Override the base authorization view from dot to
        initially create an AuthFlowUuid object for authorization
        flow tracing in logs.
        """
        # TODO: Should the client_id match a valid application here before continuing, instead of after matching to FHIR_ID?
        if not kwargs.get('is_subclass_approvalview', False):
            # Create new authorization flow trace UUID in session and AuthFlowUuid instance, if subclass is not ApprovalView
            create_session_auth_flow_trace(request)

        try:
            self.application = validate_app_is_active(request)
        except InvalidClientError as error:
            return TemplateResponse(
                request,
                "app_inactive_401.html",
                context={
                    "detail": error.error + " : " + error.description,
                },
                status=error.status_code)

        result = self.sensitive_info_check(request)

        if result:
            return result

        request.session['version'] = self.version
        # Store the lang parameter value on the server side with session keyS
        lang = request.GET.get('lang', None)
        if lang is not None and (lang == 'en' or lang == 'es'):
            request.session['auth_language'] = lang
        return super().dispatch(request, *args, **kwargs)

    def sensitive_info_check(self, request):
        result = None
        for qp in QP_CHECK_LIST:
            if request.GET.get(qp, None) is not None:
                result = HttpResponseBadRequest("Illegal query parameter [{}] detected".format(qp))
                break
        return result

    # TODO: Clean up use of the require-scopes feature flag  and multiple templates, when no longer required.
    def get_template_names(self):
        flag = get_waffle_flag_model().get("limit_data_access")
        if waffle.switch_is_active('require-scopes'):
            if flag.rollout or (flag.id is not None and self.application and flag.is_active_for_user(self.application.user)):
                return ["design_system/new_authorize_v2.html"]
            else:
                return ["design_system/authorize_v2.html"]
        else:
            if flag.rollout or (flag.id is not None and self.user and flag.is_active_for_user(self.user)):
                return ["design_system/new_authorize_v2.html"]
            else:
                return ["design_system/authorize.html"]

    def get_initial(self):
        initial_data = super().get_initial()
        initial_data["code_challenge"] = self.oauth2_data.get("code_challenge", None)
        initial_data["code_challenge_method"] = self.oauth2_data.get("code_challenge_method", None)
        return initial_data

    def get(self, request, *args, **kwargs):
        kwargs['code_challenge'] = request.GET.get('code_challenge', None)
        kwargs['code_challenge_method'] = request.GET.get('code_challenge_method', None)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        client_id = form.cleaned_data["client_id"]
        application = get_application_model().objects.get(client_id=client_id)
        credentials = {
            "client_id": form.cleaned_data.get("client_id"),
            "redirect_uri": form.cleaned_data.get("redirect_uri"),
            "response_type": form.cleaned_data.get("response_type", None),
            "state": form.cleaned_data.get("state", None),
            # "code_challenge": form.cleaned_data.get("code_challenge", None),
            # "code_challenge_method": form.cleaned_data.get("code_challenge_method", None),
        }

        if form.cleaned_data.get("code_challenge"):
            credentials["code_challenge"] = form.cleaned_data.get("code_challenge")

        if form.cleaned_data.get("code_challenge_method"):
            credentials["code_challenge_method"] = form.cleaned_data.get("code_challenge_method")

        scopes = form.cleaned_data.get("scope")
        allow = form.cleaned_data.get("allow")

        # Get beneficiary demographic scopes sharing choice
        share_demographic_scopes = form.cleaned_data.get("share_demographic_scopes")
        set_session_auth_flow_trace_value(self.request, 'auth_share_demographic_scopes', share_demographic_scopes)

        # Get scopes list available to the application
        application_available_scopes = CapabilitiesScopes().get_available_scopes(
            application=application, share_demographic_scopes=share_demographic_scopes
        )

        # Set scopes to those available to application and beneficiary demographic info choices
        scopes = ' '.join([s for s in scopes.split(" ")
                          if s in application_available_scopes])

        # Init deleted counts
        data_access_grant_delete_cnt = 0
        access_token_delete_cnt = 0
        refresh_token_delete_cnt = 0

        try:
            uri, headers, body, status = self.create_authorization_response(
                request=self.request, scopes=scopes, credentials=credentials, allow=allow
            )
        except OAuthToolkitError as error:
            response = self.error_response(error, application)

            if allow is False:
                (data_access_grant_delete_cnt,
                 access_token_delete_cnt,
                 refresh_token_delete_cnt) = remove_application_user_pair_tokens_data_access(application, self.request.user)

            beneficiary_authorized_application.send(
                sender=self,
                request=self.request,
                auth_status="FAIL",
                auth_status_code=response.status_code,
                user=self.request.user,
                application=application,
                share_demographic_scopes=share_demographic_scopes,
                scopes=scopes,
                allow=allow,
                access_token_delete_cnt=access_token_delete_cnt,
                refresh_token_delete_cnt=refresh_token_delete_cnt,
                data_access_grant_delete_cnt=data_access_grant_delete_cnt)
            return response

        # Did the beneficiary choose not to share demographic scopes, or the application does not require them?
        if share_demographic_scopes == "False" or (allow is True and application.require_demographic_scopes is False):
            (data_access_grant_delete_cnt,
             access_token_delete_cnt,
             refresh_token_delete_cnt) = remove_application_user_pair_tokens_data_access(application, self.request.user)

        beneficiary_authorized_application.send(
            sender=self,
            request=self.request,
            auth_status="OK",
            auth_status_code=None,
            user=self.request.user,
            application=application,
            share_demographic_scopes=share_demographic_scopes,
            scopes=scopes,
            allow=allow,
            access_token_delete_cnt=access_token_delete_cnt,
            refresh_token_delete_cnt=refresh_token_delete_cnt,
            data_access_grant_delete_cnt=data_access_grant_delete_cnt)

        self.success_url = uri
        log.debug("Success url for the request: {0}".format(self.success_url))

        # Extract code from url
        url_query = parse_qs(urlparse(self.success_url).query)
        code = url_query.get('code', [None])[0]

        # Get auth flow trace session values dict.
        auth_dict = get_session_auth_flow_trace(self.request)

        # We are done using auth_uuid, clear it from the session.
        cleanup_session_auth_flow_trace(self.request)

        # Update AuthFlowUuid instance with code.
        update_instance_auth_flow_trace_with_code(auth_dict, code)

        return self.redirect(self.success_url, application)


class ApprovalView(AuthorizationView):
    """
    Override the base authorization view from dot to
    use the custom AllowForm.
    """
    version = None
    form_class = SimpleAllowForm
    login_url = "/mymedicare/login"

    def __init__(self, version=1):
        self.version = version
        super().__init__()

    def dispatch(self, request, uuid, *args, **kwargs):
        # Get auth_uuid to set again after super() return. It gets cleared out otherwise.
        auth_flow_dict = get_session_auth_flow_trace(request)
        try:
            approval = Approval.objects.get(uuid=uuid)
            if approval.expired:
                raise Approval.DoesNotExist
            if approval.application\
                    and approval.application.client_id != request.GET.get('client_id', None)\
                    and approval.application.client_id != request.POST.get('client_id', None):
                raise Approval.DoesNotExist
            request.user = approval.user
        except Approval.DoesNotExist:
            pass

        # Set flag to let super method know who's calling, so auth_uuid doesn't get reset.
        kwargs['is_subclass_approvalview'] = True

        request.session['version'] = self.version

        result = super().dispatch(request, *args, **kwargs)

        if hasattr(self, 'oauth2_data'):
            application = self.oauth2_data.get('application', None)
            if application is not None:
                approval.application = self.oauth2_data.get('application', None)
                approval.save()

        # Set auth_uuid after super() return
        if auth_flow_dict:
            set_session_auth_flow_trace(request, auth_flow_dict)

        return result


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(DotTokenView):
    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request, *args, **kwargs):
        try:
            app = validate_app_is_active(request)
        except (InvalidClientError, InvalidGrantError) as error:
            return json_response_from_oauth2_error(error)

        url, headers, body, status = self.create_token_response(request)

        if status == 200:
            body = json.loads(body)
            access_token = body.get("access_token")

            dag_expiry = ""
            if access_token is not None:
                token = get_access_token_model().objects.get(
                    token=access_token)
                app_authorized.send(
                    sender=self, request=request,
                    token=token)

                if app.data_access_type == "THIRTEEN_MONTH":
                    try:
                        dag = DataAccessGrant.objects.get(
                            beneficiary=token.user,
                            application=app
                        )
                        if dag.expiration_date is not None:
                            dag_expiry = strftime('%Y-%m-%d %H:%M:%SZ', dag.expiration_date.timetuple())
                    except DataAccessGrant.DoesNotExist:
                        dag_expiry = ""

                elif app.data_access_type == "ONE_TIME":
                    expires_at = datetime.utcnow() + timedelta(seconds=body['expires_in'])
                    dag_expiry = expires_at.strftime('%Y-%m-%d %H:%M:%SZ')
                elif app.data_access_type == "RESEARCH_STUDY":
                    dag_expiry = ""

                body['access_grant_expiration'] = dag_expiry
                body = json.dumps(body)

        response = HttpResponse(content=body, status=status)
        for k, v in headers.items():
            response[k] = v
        return response


@method_decorator(csrf_exempt, name="dispatch")
class RevokeTokenView(DotRevokeTokenView):

    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request, *args, **kwargs):
        try:
            validate_app_is_active(request)
        except InvalidClientError as error:
            return json_response_from_oauth2_error(error)

        return super().post(request, args, kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class RevokeView(DotRevokeTokenView):

    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request, *args, **kwargs):
        at_model = get_access_token_model()
        try:
            app = validate_app_is_active(request)
        except (InvalidClientError, InvalidGrantError) as error:
            return json_response_from_oauth2_error(error)

        try:
            tkn = json.loads(request.body.decode("UTF-8")).get("token")
        except Exception:
            tkn = request.POST.get("token")

        escaped_tkn = html.escape(tkn)

        try:
            token = at_model.objects.get(token=tkn)
        except at_model.DoesNotExist:
            return HttpResponse(f"Token {escaped_tkn} was Not Found.  Please check the value and try again.",
                                status=status.HTTP_404_NOT_FOUND)

        try:
            dag = DataAccessGrant.objects.get(
                beneficiary=token.user,
                application=app
            )
            dag.delete()
        except DataAccessGrant.DoesNotExist:
            log.debug(f"Token deleted, but DAG lookup failed for token {escaped_tkn}.")

        return HttpResponse(content="OK", status=200)


@method_decorator(csrf_exempt, name="dispatch")
class IntrospectTokenView(DotIntrospectTokenView):

    def get(self, request, *args, **kwargs):
        try:
            validate_app_is_active(request)
        except InvalidClientError as error:
            return json_response_from_oauth2_error(error)

        return super(IntrospectTokenView, self).get(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        try:
            validate_app_is_active(request)
        except InvalidClientError as error:
            return json_response_from_oauth2_error(error)

        return super(IntrospectTokenView, self).post(request, args, kwargs)
