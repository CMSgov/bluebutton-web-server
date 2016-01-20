#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from oauth2_provider.models import AccessToken

@login_required
def authenticated_home(request):
    
    
    access_tokens = AccessToken.objects.filter(user=request.user)
    
        
    
    
    name = _("Authenticated Home")
    #this is a GET
    context= {'name':name,
              'access_tokens': access_tokens , 
              }
    return render(request, 'authenticated-home.html', context)

    
