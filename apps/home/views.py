#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
#from django.contrib import messages

@login_required
def authenticated_home(request):
    

    name = _("Authenticated Home")
    #this is a GET
    context= {'name':name,
              }
    return render(request, 'authenticated-home.html', context)

    
