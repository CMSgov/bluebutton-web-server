from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..models import UserProfile, MFACode
from ..mfa_forms import LoginForm, MFACodeForm


def mfa_code_confirm(request, uid):
    mfac = get_object_or_404(MFACode, uid=uid)
    user = mfac.user
    if request.method == 'POST':
        form = MFACodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']

            if code != mfac.code:
                mfac. tries_counter = mfac.tries_counter + 1
                if mfac.tries_counter > 3:
                    messages.error(request,
                                   _('Maximum tries reached. The authentication attempt has been invalidated.'))
                    mfac.delete()
                else:
                    mfac.save()
                messages.error(request,
                               _('The code supplied did not match what was sent. Please try again.'))

                return render(
                    request, 'generic/bootstrapform.html', {'form': form})

            if user.is_active:
                # Fake backend here since its not needed.
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                # Else, just login as normal without MFA
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
                messages.error(request,
                               _('Your account has not been activated. Please check your email for a link to '
                                 'activate your account.'))
                return render(
                    request, 'generic/bootstrapform.html', {'form': form})

        else:
            return render(request, 'generic/bootstrapform.html',
                          {'form': form})
    # this is a GET
    return render(request, 'generic/bootstrapform.html',
                  {'form': MFACodeForm()})


def mfa_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:

                if user.is_active:
                    # Get User profile
                    up, g_o_c = UserProfile.objects.get_or_create(user=user)
                    # If MFA, send code and redirect
                    if up.mfa_login_mode in ("SMS", "EMAIL"):
                        # Create an MFA message
                        mfac = MFACode.objects.create(
                            user=up.user, mode=up.mfa_login_mode)
                        # Send code and redirect
                        if up.mfa_login_mode == "SMS":
                            messages.info(request,
                                          _('An access code was sent to your mobile device. Please enter it here.'))
                        if up.mfa_login_mode == "EMAIL":
                            messages.info(request,
                                          _('An access code was sent to your email. Please enter it here.'))
                        return HttpResponseRedirect(reverse('mfa_code_confirm',
                                                            args=(mfac.uid,)))
                    # Else, just login as normal without MFA
                    login(request, user)
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
                messages.error(request, _('Invalid username or password.'))
                return render(request, 'login.html', {'form': form})
        else:
            return render(request, 'login.html', {'form': form})
    # this is a GET
    return render(request, 'login.html', {'form': LoginForm()})
