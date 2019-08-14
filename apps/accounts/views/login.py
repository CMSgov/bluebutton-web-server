from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from sys import version_info
from ..forms import AuthenticationForm
from ..models import UserProfile


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
