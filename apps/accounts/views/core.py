import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from ..forms import (RequestInviteForm, AccountSettingsForm,
                     LoginForm,
                     SignupForm)
from ..models import *
from ..utils import validate_activation_key
from django.conf import settings

logger = logging.getLogger('hhs_server.%s' % __name__)


def request_invite(request):
    name = 'Request a Developer Invite to the %s' % (
        settings.ORGANIZATION_NAME)
    if request.method == 'POST':
        form = RequestInviteForm(request.POST)
        if form.is_valid():

            invite_request = form.save()
            messages.success(
                request,
                _('Your invite request has been received.  '
                  'You will be contacted by email when your '
                  'invitation is ready.'),
            )

            logger.debug("email to invite:%s" % invite_request.email)

            if settings.MFA:
                return HttpResponseRedirect(reverse('mfa_login'))
            else:
                return HttpResponseRedirect(reverse('login'))
        else:
            return render(request, 'generic/bootstrapform.html', {
                'name': name,
                'form': form,
            })
    else:
        # this is an HTTP  GET
        return render(request,
                      'generic/bootstrapform.html',
                      {'name': name,
                       'form': RequestInviteForm()})


def mylogout(request):
    logout(request)
    messages.success(request, _('You have been logged out.'))
    if settings.MFA:
        return HttpResponseRedirect(reverse('mfa_login'))
    else:
        return HttpResponseRedirect(reverse('login'))


def simple_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:

                if user.is_active:
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


@login_required
def display_api_keys(request):
    up = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'display-api-keys.html', {'up': up})


@login_required
def reissue_api_keys(request):
    up = get_object_or_404(UserProfile, user=request.user)
    up.access_key_reset = True
    up.save()
    messages.success(request, _('Your API credentials have been reissued.'))
    return HttpResponseRedirect(reverse('display_api_keys'))


def create_account(request):

    name = "Create a Developer Account"

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,
                             _("Your account was created. Please "
                               "check your email to verify your account."))

            if settings.MFA:
                return HttpResponseRedirect(reverse('mfa_login'))
            else:
                return HttpResponseRedirect(reverse('login'))
        else:
            # return the bound form with errors
            return render(request,
                          'generic/bootstrapform.html',
                          {'name': name, 'form': form})
    else:
        # this is an HTTP  GET
        messages.info(request,
                      _("An invitation code is required to register."))
        return render(request,
                      'generic/bootstrapform.html',
                      {'name': name, 'form': SignupForm()})


@login_required
def account_settings(request):
    name = _('Account Settings')
    up = get_object_or_404(UserProfile, user=request.user)

    groups = request.user.groups.values_list('name', flat=True)
    for g in groups:
        messages.info(request, _('You are in the group: %s' % (g)))

    if request.method == 'POST':
        form = AccountSettingsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # update the user info
            request.user.username = data['username']
            request.user.email = data['email']
            request.user.first_name = data['first_name']
            request.user.last_name = data['last_name']
            request.user.save()
            # update the user profile
            up.organization_name = data['organization_name']
            up.create_applications = data['create_applications']
            up.mfa_login_mode = data['mfa_login_mode']
            up.mobile_phone_number = data['mobile_phone_number']
            up.save()
            messages.success(request,
                             'Your account settings have been updated.')
            return render(request,
                          'account-settings.html',
                          {'form': form, 'name': name})
        else:
            # the form had errors
            return render(request,
                          'account-settings.html',
                          {'form': form, 'name': name})

    # this is an HTTP GET
    form = AccountSettingsForm(
        initial={
            'username': request.user.username,
            'email': request.user.email,
            'organization_name': up.organization_name,
            'mfa_login_mode': up.mfa_login_mode,
            'mobile_phone_number': up.mobile_phone_number,
            'create_applications': up.create_applications,
            'last_name': request.user.last_name,
            'first_name': request.user.first_name,
            'access_key_reset': up.access_key_reset,
        }
    )
    return render(request,
                  'account-settings.html',
                  {'name': name, 'form': form})


def activation_verify(request, activation_key):
    if validate_activation_key(activation_key):
        messages.success(request,
                         'Your account has been activated. You may now login.')
    else:
        messages.error(request,
                       'This key does not exist or has already been used.')
    if settings.MFA:
        return HttpResponseRedirect(reverse('mfa_login'))
    else:
        return HttpResponseRedirect(reverse('login'))
