#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST, require_GET
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from ..emails import send_invite_request_notices
from ..forms import *
from ..models import *
from ..utils import validate_activation_key 

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
            return render(request, 'generic/bootstrapform.html', {'name': name,'form': form})
    else:
       #this is an HTTP  GET
       return render(request,'generic/bootstrapform.html',
                    {'name': name, 'form': RequestInviteForm()})

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
                        _("Please check your email for a link to activate your account."))

                   return render(request, 'login.html', {'form': form})
            else:
                messages.error(request, _("Invalid username or password."))

                return render(request, 'login.html',{'form': form})

        else:
         return render(request, 'login.html',{'form': form})
    #this is a GET
    return render(request, 'login.html', {'form': LoginForm()})


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
            return render(request, 'reset-password.html',
                          {'form': form,
                           'reset_password_key': reset_password_key })

    return render(request, 'reset-password.html',
                  {'form': PasswordResetForm(),
                   'reset_password_key': reset_password_key })

@login_required
def display_api_keys(request):

    up = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'display-api-keys.html',{'up': up})

@login_required
def reissue_api_keys(request):

    up = get_object_or_404(UserProfile, user=request.user)
    up.access_key_reset = True
    up.save()
    messages.success(request, _("Your API credentials have been reissued."))
    return HttpResponseRedirect(reverse('display_api_keys'))



def forgot_password(request):
    name=_("Forgot Password")
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
             return render(request,'generic/bootstrapform.html', {'name': name,'form': form})

    else:
        return render(request, 'generic/bootstrapform.html',
                             {'name': name, 'form': PasswordResetRequestForm()})




def create(request):
    name = "Create a Blue Button Developer Account"
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
          new_user = form.save()
          messages.success(request, _("Your account was created. Please check your email to verify your account."))
          return HttpResponseRedirect(reverse('login'))
        else:
            #return the bound form with errors
            return render(request, 'generic/bootstrapform.html',
                     {'name': name,'form': form})
    else:
       #this is an HTTP  GET
       messages.info(request, _("An invitation code is required to register."))
       return render(request,'generic/bootstrapform.html',
                               {'name': name, 'form': SignupForm()})


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
            return render(request, 'generic/bootstrapform.html',
                        {'form': form, 'name': name })
        else:
            #the form had errors
            return render(request,'generic/bootstrapform.html',
                            {'form': form,'name': name })


    #this is an HTTP GET
    return render(request, 'generic/bootstrapform.html',
                              {'name': name, 'form': AccountSettingsForm(
                              initial={ 'username':  request.user.username,
                                'email':                    request.user.email,
                                'organization_name':        up.organization_name,
                                'last_name':                request.user.last_name,
                                'first_name':               request.user.first_name,
                                'access_key_reset':         up.access_key_reset,
                                })})


def activation_verify(request, activation_key):

    if validate_activation_key(activation_key):
        messages.success(request, "Your account has been activated and you may now login.")
    else:
        messages.error(request, "This key does not exist or has already been used.")

    return HttpResponseRedirect(reverse('login'))
