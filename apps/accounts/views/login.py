from axes.decorators import axes_dispatch
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.password_validation import get_default_password_validators
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from ..forms import AuthenticationForm
from ..validators import PasswordReuseAndMinAgeValidator


class LoginView(LoginView):
    """
    Custom Django login view.
    """
    authentication_form = AuthenticationForm

    @method_decorator(axes_dispatch)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Extend django login view to do password expire check
        and redirect to password-change instead of user account home
        """
        # auth_login(self.request, form.get_user())
        response = super().form_valid(form)
        if response.status_code == 302:
            passwd_validators = get_default_password_validators()
            the_validator = None
            for v in passwd_validators:
                if isinstance(v, PasswordReuseAndMinAgeValidator):
                    the_validator = v
                    break
            if the_validator is not None and the_validator.password_expired(form.get_user()):
                return HttpResponseRedirect(reverse("expired_password_change"))
        return response


class PasswordChangeView(PasswordChangeView):
    """
    Custom Django password change view.
    """
    @method_decorator(axes_dispatch)
    def dispatch(self, request, *args, **kwargs):
        if "expired-password-change" in request.path:
            messages.warning(self.request, 'Your password has expired, change password strongly recommended.')
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(login_required)
    def form_valid(self, form):
        messages.success(self.request, 'Your password was updated.')
        return super().form_valid(form)
