import logging
from oauth2_provider.views.base import AuthorizationView as DotAuthorizationView
from ..forms import SimpleAllowForm
from ..models import Approval

logger = logging.getLogger('hhs_server.%s' % __name__)


class AuthorizationView(DotAuthorizationView):
    """
    Override the base authorization view from dot to
    use the custom AllowForm.
    """
    form_class = SimpleAllowForm
    login_url = "/mymedicare/login"
    template_name = "design_system/authorize.html"


class ApprovalView(DotAuthorizationView):
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
