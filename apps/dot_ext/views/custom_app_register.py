#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from ..forms import CustomRegisterApplicationForm


@login_required
def RegisterApplication(request):
    template_name = "oauth2_provider/application_registration_form.html"
    if request.method == 'POST':
        form = CustomRegisterApplicationForm(request.user, request.POST)
        if form.is_valid():
            cra = form.save(commit = False)
            cra.user=request.user
            cra.save()
            return HttpResponseRedirect(reverse('oauth2_provider:list'))
        else:
            #The form is invalid
             return render( request, template_name, {'form': form})
    else:
        #A GET
        return render( request, template_name, {'form': CustomRegisterApplicationForm(request.user)})
