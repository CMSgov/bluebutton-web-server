from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..models import UserProfile, MFACode
from ..mfa_forms import LoginForm, MFACodeForm
import logging
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from ...utils import get_client_ip
import sys
from django.views.decorators.cache import never_cache
from axes.decorators import axes_dispatch


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
                    request, 'generic/bootstrapform.html', {'form': form})

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
                    request, 'generic/bootstrapform.html', {'form': form})
        else:
            return render(request, 'generic/bootstrapform.html',
                          {'form': form})
    # this is a GET
    return render(request, 'generic/bootstrapform.html',
                  {'form': MFACodeForm()})


@never_cache
@axes_dispatch
def mfa_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # If username doesn't exist, try username matching email address.
            try:
                User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                try:
                    check_user = User.objects.get(email__iexact=username)
                    username = check_user.username
                except User.DoesNotExist:
                    pass

            user = authenticate(request=request, username=username.lower(), password=password)

            if user is not None:

                if user.is_active:
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
                                request, _('An access code was sent to your email. Please enter it here.'))
                        rev = reverse('mfa_code_confirm', args=(mfac.uid,))
                        # Fetch the next and urlencode
                        if request.GET.get('next', ''):
                            if sys.version_info[0] == 3:
                                import urllib.request as req
                                rev = "%s?next=%s" % (
                                    rev, req.pathname2url(request.GET.get('next', '')))
                            if sys.version_info[0] == 2:
                                import urllib
                                rev = "%s?next=%s" % (
                                    rev, urllib.pathname2url(request.GET.get('next', '')))

                        return HttpResponseRedirect(rev)
                    # Else, just login as normal without MFA
                    # User's AAL is single factor
                    up.aal = '1'
                    up.save()
                    login(request, user)
                    logger.info(
                        "Successful login from {}".format(
                            get_client_ip(request)))
                    next_param = request.GET.get('next', '')
                    if next_param:
                        # If a next is in the URL, then go there
                        return HttpResponseRedirect(next_param)
                    # otherwise just go to home.
                    return HttpResponseRedirect(reverse('home'))
                else:
                    # The user exists but is_active=False
                    messages.error(request,
                                   _('Please check your email for a link to '
                                     'activate your account.'))
                    return render(request, 'login.html', {'form': form})
            else:
                logger.info("Invalid login attempt.")
                messages.error(request, _('Invalid email or password.'))
                return render(request, 'login.html', {'form': form})
        else:
            return render(request, 'login.html', {'form': form})
    # this is a GET
    return render(request, 'login.html', {'form': LoginForm()})
