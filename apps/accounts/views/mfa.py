from django.contrib.auth import login
from django.contrib.auth.signals import user_login_failed
from django.contrib import messages
from django.dispatch import receiver
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from ..mfa_forms import MFACodeForm
from ..models import UserProfile, MFACode
import logging


logger = logging.getLogger('hhs_oauth_server.accounts')
failed_login_log = logging.getLogger('unsuccessful_logins')


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, **kwargs):
    lw = "Login failed for %s." % (credentials['username'])
    failed_login_log.warning(lw)


@never_cache
def mfa_code_confirm(request, uid):
    mfac = get_object_or_404(MFACode, uid=uid)
    user = mfac.user
    if request.method == 'POST':
        form = MFACodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']

            if code != mfac.code:
                mfac.tries_counter = mfac.tries_counter + 1
                if mfac.tries_counter > 3:
                    messages.error(
                        request,
                        _('Maximum tries reached. The authentication attempt has been invalidated.'))
                    mfac.delete()
                else:
                    mfac.save()
                messages.error(
                    request, _('The code supplied did not match what was sent. Please try again.'))

                return render(
                    request, 'registration/mfa.html', {'form': form})

            if user.is_active:
                # Fake backend here since its not needed.
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                # User's AAL is 2 factor
                up = UserProfile.objects.get(user=user)
                up.aal = '2'
                up.save()
                login(request, user)
                mfac.delete()
                next_param = request.GET.get('next', '')
                if next_param:
                    # If a next is in the URL, then go there
                    return HttpResponseRedirect(next_param)
                # otherwise just go to home.
                return HttpResponseRedirect(reverse('home'))
            else:
                # The user exists but is_active=False
                messages.error(
                    request, _(
                        'Your account has not been activated. Please check your email for a link to '
                        'activate your account.'))
                return render(
                    request, 'registration/mfa.html', {'form': form})
        else:
            return render(request, 'registration/mfa.html',
                          {'form': form})
    # this is a GET
    return render(request, 'registration/mfa.html',
                  {'form': MFACodeForm()})
