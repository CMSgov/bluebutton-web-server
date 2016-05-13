#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.http import HttpResponseNotAllowed,  HttpResponseForbidden
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Sum
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .emails import send_invite_request_notices
from .forms import *
from .models import *
from .utils import verify

from oauth2_provider.decorators import protected_resource


def request_invite(request):
    name='Request an Invite'
    if request.method == 'POST':
        form = RequestInviteForm(request.POST)
        if form.is_valid():
          invite_request = form.save()

          send_invite_request_notices(invite_request)

          messages.success(request, _("Your invite request has been received.  You will be contacted by email when your invitation is ready."))
          return HttpResponseRedirect(reverse('login'))
        else:
            return render_to_response('generic/bootstrapform.html',
                                      RequestContext(request, {'name': name,'form': form}))
    else:
       #this is an HTTP  GET
       return render_to_response('generic/bootstrapform.html',
                                 RequestContext(request, {'name': name, 'form': RequestInviteForm()}))



def mylogout(request):
    logout(request)
    messages.success(request, _("You have been logged out."))
    return HttpResponseRedirect(reverse('login'))


def simple_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user=authenticate(username=username, password=password)

            if user is not None:

                if user.is_active:
                    login(request,user)

                    next = request.GET.get('next','')
                    if next:
                        #If a next is in the URL, then go there
                        return HttpResponseRedirect(next)
                    #otherwise just go to home.
                    return HttpResponseRedirect(reverse('home'))
                else:
                   #The user exists but is_active=False
                   messages.error(request,
                        _("Your account is inactive so you may not log in."))

                   return render_to_response('login.html',
                                            {'form': form},
                                            RequestContext(request))
            else:
                messages.error(request, _("Invalid username or password."))

                return render_to_response('login.html',
                                    {'form': form},
                                    RequestContext(request))

        else:
         return render_to_response('login.html',
                              RequestContext(request, {'form': form}))
    #this is a GET
    return render_to_response('login.html',
                              {'form': LoginForm()},
                              context_instance = RequestContext(request))




def reset_password(request, reset_password_key=None):

    vprk = get_object_or_404(ValidPasswordResetKey, reset_password_key=reset_password_key)
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            vprk.user.set_password(form.cleaned_data['password1'])
            vprk.user.save()
            vprk.delete()
            logout(request)
            messages.success(request, _("Your password has been reset."))
            return HttpResponseRedirect(reverse('login'))
        else:
            return render_to_response('reset-password.html',
                        RequestContext(request, {'form': form,
                            'reset_password_key': reset_password_key}))

    return render_to_response('reset-password.html',
                              RequestContext(request,
                                    {'form': PasswordResetForm(),
                                    'reset_password_key': reset_password_key}))

@login_required
def display_api_keys(request):

    up = get_object_or_404(UserProfile, user=request.user)
    return render_to_response('display-api-keys.html',
                              RequestContext(request,
                                    {'up': up}))

@login_required
def reissue_api_keys(request):

    up = get_object_or_404(UserProfile, user=request.user)
    up.access_key_reset = True
    up.save()
    messages.success(request, _("Your API credentials have been reissued."))
    return HttpResponseRedirect(reverse('display_api_keys'))



def password_reset_request(request):
    if request.method == 'POST':

        form = PasswordResetRequestForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            try:
                u=User.objects.get(email=data['email'])
            except(User.DoesNotExist):
                messages.error(request, "A user with the email supplied does not exist.")
                return HttpResponseRedirect(reverse('password_reset_request'))
            #success
            k=ValidPasswordResetKey.objects.create(user=u)
            messages.info(request, "Please check your email for a special link to rest your password.")
            return HttpResponseRedirect(reverse('login'))

        else:
             return render_to_response('generic/bootstrapform.html',
                                      RequestContext(request, {'form': form}))

    else:
        return render_to_response('password-reset-request.html',
                             {'form': PasswordResetRequestForm()},
                              context_instance = RequestContext(request))




def create(request):
    name = "Create an CMS Developer Account"
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
          new_user = form.save()
          up, created = UserProfile.objects.get_or_create(user=new_user)
          messages.success(request, _("Account created. What are you waiting for? Log in!"))
          return HttpResponseRedirect(reverse('login'))
        else:
            #return the bound form with errors
            return render_to_response('generic/bootstrapform.html',
                                      RequestContext(request, {'name': name,
                                                               'form': form}))
    else:
       #this is an HTTP  GET
       messages.info(request, _("An invitation code is required to register."))
       return render_to_response('generic/bootstrapform.html',
                                 RequestContext(request,
                                {'name': name,
                                 'form': SignupForm()}))


def verify_email(request, verification_key,
                 template_name='activate.html',
                 extra_context=None):
    verification_key = verification_key.lower() # Normalize before trying anything with it.
    account = verify(verification_key)

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(template_name,
                              { 'account': account},
                              context_instance=context)



@login_required
def account_settings(request):
    name = _("Account Settings")
    up = get_object_or_404(UserProfile, user=request.user)

    groups = request.user.groups.values_list('name',flat=True)
    for g in groups:
        messages.info(request, _("You are in the group: %s" % (g)))    

    if request.method == 'POST':
        form = AccountSettingsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            #update the user info
            request.user.username       = data['username']
            request.user.email          = data['email']
            request.user.first_name     = data['first_name']
            request.user.last_name      = data['last_name']
            request.user.save()
            #update the user profile
            up.organization_name        = data['organization_name']
            up.save()
            messages.success(request,'Your account settings have been updated.')
            return render_to_response('generic/bootstrapform.html',
                            {'form': form,
                             'name': name,
                             },
                            RequestContext(request))
        else:
            #the form had errors
            return render_to_response('generic/bootstrapform.html',
                            {'form': form,
                             'name': name,
                             },
                            RequestContext(request))


    #this is an HTTP GET
    return render_to_response('generic/bootstrapform.html',
                    {'name': name, 'form': AccountSettingsForm(
                              initial={ 'username':  request.user.username,
                                'email':                    request.user.email,
                                'organization_name':        up.organization_name,
                                'last_name':                request.user.last_name,
                                'first_name':               request.user.first_name,
                                'access_key_reset':         up.access_key_reset,
                                })},
                              RequestContext(request))


def signup_verify(request, signup_key=None):

    if validate_signup(signup_key=signup_key):
        messages.success(request, "Your account has been activated. You may now login.")
        return HttpResponseRedirect(reverse('login'))
    else:
        return render_to_response('invalid-key.html',
                              RequestContext(request,
                                             {}))


@require_GET
@protected_resource()
def user_self(request):
    """
    Views that returns a json representation of the current user's details.
    """
    user = request.resource_owner
    data = {
        'id': user.pk,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'created': user.date_joined,
    }
    return JsonResponse(data)
