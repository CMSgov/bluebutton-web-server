import json
import logging
import waffle
from oauth2_provider.views.introspect import IntrospectTokenView as DotIntrospectTokenView
from oauth2_provider.views.base import AuthorizationView as DotAuthorizationView
from oauth2_provider.views.base import TokenView as DotTokenView
from oauth2_provider.views.base import RevokeTokenView as DotRevokeTokenView
from oauth2_provider.models import get_application_model
from oauth2_provider.exceptions import OAuthToolkitError
from apps.dot_ext.scopes import CapabilitiesScopes

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters

from urllib.parse import urlparse, parse_qs
from ..signals import beneficiary_authorized_application
from ..forms import SimpleAllowForm
from ..loggers import (create_session_auth_flow_trace, cleanup_session_auth_flow_trace,
                       get_session_auth_flow_trace, set_session_auth_flow_trace,
                       set_session_auth_flow_trace_value, update_instance_auth_flow_trace_with_code)
from ..models import Approval
from ..utils import remove_application_user_pair_tokens_data_access
from ..utils import validate_app_is_active

from rest_framework.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponse


log = logging.getLogger('hhs_server.%s' % __name__)


class AuthorizationView(DotAuthorizationView):
    """
    Override the base authorization view from dot to
    use the custom AllowForm.
    """
    form_class = SimpleAllowForm
    login_url = "/mymedicare/login"

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
            validate_app_is_active(request)
        except PermissionDenied as error:
            return TemplateResponse(
                request,
                "app_inactive_403.html",
                context={
                    "detail": error.detail,
                },
                status=error.status_code)

        return super().dispatch(request, *args, **kwargs)

    # TODO: Clean up use of the require-scopes feature flag  and multiple templates, when no longer required.
    def get_template_names(self):
        if waffle.switch_is_active('require-scopes'):
            return ["design_system/authorize_v2.html"]
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
            "code_challenge": form.cleaned_data.get("code_challenge", None),
            "code_challenge_method": form.cleaned_data.get("code_challenge_method", None),
        }
        scopes = form.cleaned_data.get("scope")
        allow = form.cleaned_data.get("allow")

        # Get beneficiary demographic scopes sharing choice
        share_demographic_scopes = form.cleaned_data.get("share_demographic_scopes")
        set_session_auth_flow_trace_value(self.request, 'auth_share_demographic_scopes', share_demographic_scopes)

        # Get scopes list available to the application
        application_available_scopes = CapabilitiesScopes().get_available_scopes(application=application)

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
    form_class = SimpleAllowForm
    login_url = "/mymedicare/login"

    def dispatch(self, request, uuid, *args, **kwargs):
        # Get auth_uuid to set again after super() return. It gets cleared out otherwise.
        auth_flow_dict = get_session_auth_flow_trace(request)

        # trows DoesNotExist
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
            validate_app_is_active(request)
        except PermissionDenied as error:
            return HttpResponse(json.dumps({"status_code": error.status_code,
                                            "detail": error.detail, }),
                                status=error.status_code,
                                content_type='application/json')

        return super().post(request, args, kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class RevokeTokenView(DotRevokeTokenView):

    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request, *args, **kwargs):
        try:
            validate_app_is_active(request)
        except PermissionDenied as error:
            return HttpResponse(json.dumps({"status_code": error.status_code,
                                            "detail": error.detail, }),
                                status=error.status_code,
                                content_type='application/json')

        return super().post(request, args, kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class IntrospectTokenView(DotIntrospectTokenView):

    def get(self, request, *args, **kwargs):
        try:
            validate_app_is_active(request)
        except PermissionDenied as error:
            return HttpResponse(json.dumps({"status_code": error.status_code,
                                            "detail": error.detail, }),
                                status=error.status_code,
                                content_type='application/json')

        return super(IntrospectTokenView, self).get(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        try:
            validate_app_is_active(request)
        except PermissionDenied as error:
            return HttpResponse(json.dumps({"status_code": error.status_code,
                                            "detail": error.detail, }),
                                status=error.status_code,
                                content_type='application/json')

        return super(IntrospectTokenView, self).post(request, args, kwargs)
