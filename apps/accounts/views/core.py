import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..forms import (AccountSettingsForm,
                     SignupForm)
from ..models import UserProfile
from ..utils import validate_activation_key
from django.conf import settings
from django.views.decorators.cache import never_cache

logger = logging.getLogger('hhs_server.%s' % __name__)


def create_account(request):

    name = "Create your %s Account" % settings.APPLICATION_TITLE

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,
                             _("Your account was created. Please "
                               "check your email to verify your account "
                               "before logging in."))
            return pick_reverse_login()
        else:
            # return the bound form with errors
            return render(request,
                          'registration/signup.html',
                          {'name': name, 'form': form})
    else:
        return render(request,
                      'registration/signup.html',
                      {'name': name, 'form': SignupForm()})


@never_cache
@login_required
def account_settings(request):
    name = _('Account Settings')
    up, created = UserProfile.objects.get_or_create(user=request.user)

    if settings.DEBUG:
        # Display all the groups the user is in.
        groups = request.user.groups.values_list('name', flat=True)
        for g in groups:
            messages.info(request, _('You are in the group: %s' % (g)))

    if request.method == 'POST':
        form = AccountSettingsForm(request.POST, request=request)
        if form.is_valid():
            data = form.cleaned_data
            # update the user info
            request.user.first_name = data['first_name']
            request.user.last_name = data['last_name']
            request.user.save()
            # update the user profile
            up.organization_name = data['organization_name']
            up.mfa_login_mode = data['mfa_login_mode']
            up.create_applications = data['create_applications']
            up.authorize_applications = True
            up.save()
            messages.success(request,
                             'Your account settings have been updated.')
            return HttpResponseRedirect(reverse('account_settings'))

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
            'create_applications': up.create_applications,
            'last_name': request.user.last_name,
            'first_name': request.user.first_name,
            'access_key_reset': up.access_key_reset,
        }, request=request
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
    return pick_reverse_login()


def pick_reverse_login():
    """
    settings.MFA should be True or False
    Check settings.MFA to determine which reverse call to make
    :return:
    """
    return HttpResponseRedirect(reverse('login'))
