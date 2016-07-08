from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from ..forms import *
from ..models import *
from ..emails import send_invite_request_notices
from ..utils import validate_activation_key


def request_developer_invite(request):
    name = 'Request a Developer Invite to the CMS Blue Button API'
    additional_info = """
    <p>The CMS Blue Button API is a new feature from Medicare. CMS Blue Button
    API enables beneficiaries to connect their data to applications and
    research programs they trust.</p>
    <p>Register an account and an application and you can empower beneficiaries
    to download their claims information to the innovative apps you create
    to help them stay healthy.</p>
    <p>We are rolling out CMS Blue Button API in phases to gather feedback on
    the new features. To become a CMS Blue Button API developer you must
    request an invitation code by filling in this form. We will send you an
    email with the invitation link.</p>
    <h4>Let's get started...</h4>
    """
    # FIXME: variable not used
    # u_type = 'DEV'
    if request.method == 'POST':
        form = RequestDeveloperInviteForm(request.POST)
        if form.is_valid():
            invite_request = form.save()

            send_invite_request_notices(invite_request)

            messages.success(
                request,
                _('Your invite request has been received.  '
                  'You will be contacted by email when your '
                  'invitation is ready.'),
            )
            return HttpResponseRedirect(reverse('login'))
        else:
            return render(request, 'generic/bootstrapform.html', {
                'name': name,
                'form': form,
                'additional_info': additional_info,
            })
    else:
        # this is an HTTP  GET
        return render(request,
                      'generic/bootstrapform.html',
                      {'name': name,
                       'form': RequestDeveloperInviteForm(),
                       'additional_info': additional_info})


def request_user_invite(request):
    name = 'Request an Invite to CMS Blue Button API'
    additional_info = """
    <p>CMS Blue Button API is a new feature from Medicare. CMS Blue Button API
    connects your data to applications and research programs you trust.</p>
    <p>Authorize an application and it will download data automatically on
    your behalf.</p>
    <p>We are rolling out CMS Blue Button API in phases to gather feedback on
    the new features. To try CMS Blue Button API for yourself you must request
    an invitation code by filling in this form. We will send you an email
    with the invitation link. You must click on the link in the email to
    add the CMS Blue Button API to your Medicare account.</p>
    <h4>Let's get started...</h4>
    """
    # FIXME: variable not used
    # u_type = 'BEN'
    if request.method == 'POST':
        form = RequestUserInviteForm(request.POST)
        if form.is_valid():
            invite_request = form.save()

            send_invite_request_notices(invite_request)

            messages.success(
                request,
                _('Your invite request has been received.  '
                  'You will be contacted by email when your '
                  'invitation is ready.'),
            )
            return HttpResponseRedirect(reverse('login'))
        else:
            return render(request,
                          'generic/bootstrapform.html',
                          {'name': name,
                           'form': form,
                           'additional_info': additional_info})
    else:
        # this is an HTTP  GET
        return render(request,
                      'generic/bootstrapform.html',
                      {'name': name,
                       'form': RequestUserInviteForm(),
                       'additional_info': additional_info})


def mylogout(request):
    logout(request)
    messages.success(request, _('You have been logged out.'))
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


def password_reset_email_verify(request, reset_password_key=None):
    vprk = get_object_or_404(ValidPasswordResetKey,
                             reset_password_key=reset_password_key)
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            vprk.user.set_password(form.cleaned_data['password1'])
            vprk.user.save()
            vprk.delete()
            logout(request)
            messages.success(request, _('Your password has been reset.'))
            return HttpResponseRedirect(reverse('login'))
        else:
            return render(request,
                          'generic/bootstrapform.html',
                          {'form': form,
                           'reset_password_key': reset_password_key})

    return render(request,
                  'generic/bootstrapform.html',
                  {'form': PasswordResetForm(),
                   'reset_password_key': reset_password_key})


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


def forgot_password(request):
    name = _('Forgot Password')
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            try:
                u = User.objects.get(email=data['email'])
            except(User.DoesNotExist):
                messages.error(request,
                               'A user with the email supplied '
                               'does not exist.')
                return HttpResponseRedirect(reverse('password_reset_request'))
            # success
            ValidPasswordResetKey.objects.create(user=u)
            messages.info(request,
                          'Please check your email for a special link'
                          ' to reset your password.')
            return HttpResponseRedirect(reverse('login'))
        else:
            return render(request,
                          'generic/bootstrapform.html',
                          {'name': name, 'form': form})

    else:
        return render(request,
                      'generic/bootstrapform.html',
                      {'name': name, 'form': PasswordResetRequestForm()})


def create_developer(request):

    name = "Create a Developer Account"

    if request.method == 'POST':
        form = SignupDeveloperForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,
                             _("Your developer account was created. Please "
                               "check your email to verify your account."))
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
                      {'name': name, 'form': SignupDeveloperForm()})


def create_user(request):
    name = "Create a CMS Blue Button API Account"

    if request.method == 'POST':
        form = SignupUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,
                             _("Your account was created. Please check your "
                               "email to verify your account."))
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
                      {'name': name, 'form': SignupUserForm()})


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
            up.save()
            messages.success(request,
                             'Your account settings have been updated.')
            return render(request,
                          'generic/bootstrapform.html',
                          {'form': form, 'name': name})
        else:
            # the form had errors
            return render(request,
                          'generic/bootstrapform.html',
                          {'form': form, 'name': name})

    # this is an HTTP GET
    form = AccountSettingsForm(
        initial={
            'username': request.user.username,
            'email': request.user.email,
            'organization_name': up.organization_name,
            'last_name': request.user.last_name,
            'first_name': request.user.first_name,
            'access_key_reset': up.access_key_reset,
        }
    )
    return render(request,
                  'generic/bootstrapform.html',
                  {'name': name, 'form': form})


def activation_verify(request, activation_key):
    if validate_activation_key(activation_key):
        messages.success(request,
                         'Your account has been activated. You may now login.')
    else:
        messages.error(request,
                       'This key does not exist or has already been used.')

    return HttpResponseRedirect(reverse('login'))
