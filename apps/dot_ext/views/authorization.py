import logging
from oauth2_provider.views.base import AuthorizationView as DotAuthorizationView
from oauth2_provider.models import get_application_model
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.signals import app_authorized
from ..forms import SimpleAllowForm
from ..models import Approval

log = logging.getLogger('hhs_server.%s' % __name__)


class AuthorizationView(DotAuthorizationView):
    """
    Override the base authorization view from dot to
    use the custom AllowForm.
    """
    form_class = SimpleAllowForm
    login_url = "/mymedicare/login"
    template_name = "design_system/authorize.html"

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

        try:
            uri, headers, body, status = self.create_authorization_response(
                request=self.request, scopes=scopes, credentials=credentials, allow=allow
            )
        except OAuthToolkitError as error:
            return self.error_response(error, application)

        app_authorized.send(
            sender=self,
            request=self.request,
            token=None,
            application=application)

        self.success_url = uri
        log.debug("Success url for the request: {0}".format(self.success_url))
        return self.redirect(self.success_url, application)


class ApprovalView(AuthorizationView):
    """
    Override the base authorization view from dot to
    use the custom AllowForm.
    """
    form_class = SimpleAllowForm
    login_url = "/mymedicare/login"
    template_name = "design_system/authorize.html"

    def dispatch(self, request, uuid, *args, **kwargs):
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

        result = super(ApprovalView, self).dispatch(request, *args, **kwargs)

        application = self.oauth2_data.get('application', None)
        if application is not None:
            approval.application = self.oauth2_data.get('application', None)
            approval.save()

        return result
