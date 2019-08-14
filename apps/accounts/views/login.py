from axes.decorators import axes_dispatch
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib import messages
from django.utils.decorators import method_decorator
from ..forms import AuthenticationForm


class LoginView(LoginView):
    """
    Custom Django login view.
    """
    authentication_form = AuthenticationForm

    @method_decorator(axes_dispatch)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class PasswordChangeView(PasswordChangeView):
    """
    Custom Django password change view.
    """
    @method_decorator(login_required)
    def form_valid(self, form):
        messages.success(self.request, 'Your password was updated.')
        return super().form_valid(form)
