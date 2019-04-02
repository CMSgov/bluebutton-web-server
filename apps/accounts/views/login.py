from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from sys import version_info
from ..forms import AuthenticationForm
from ..models import UserProfile, MFACode


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
        Security check complete. MFA login redirect or login
        """
        mfa_redirect = self.get_mfa_redirect(form.get_user())
        if mfa_redirect:
            return HttpResponseRedirect(mfa_redirect)
        else:
            return super().form_valid(form)

    def get_mfa_redirect(self, user):
        if getattr(user, 'is_active', None):
            # Get User profile
            up, g_o_c = UserProfile.objects.get_or_create(user=user)
            # If MFA, send code and redirect
            if up.mfa_login_mode in ("EMAIL",) and settings.MFA:
                # Create an MFA message
                mfac = MFACode.objects.create(
                    user=up.user, mode=up.mfa_login_mode)
                # Send code and redirect
                if up.mfa_login_mode == "EMAIL":
                    messages.info(
                        self.request, _('An access code was sent to your email. Please enter it here.'))

                    rev = reverse('mfa_code_confirm', args=(mfac.uid,))

                    # Fetch the next and urlencode
                    if self.request.GET.get('next', ''):
                        if version_info[0] == 3:
                            import urllib.request as req
                            rev = "%s?next=%s" % (
                                rev, req.pathname2url(self.request.GET.get('next', '')))
                        if version_info[0] == 2:
                            import urllib
                            rev = "%s?next=%s" % (
                                rev, urllib.pathname2url(self.request.GET.get('next', '')))

                    return rev
            else:
                # User's AAL is single factor
                up.aal = '1'
                up.save()
        return None
