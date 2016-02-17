#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.forms import ModelForm
from django.contrib.auth.models import Group
from django import forms
from oauth2_provider.models import get_application_model
from django.utils.translation import ugettext_lazy as _
from ..capabilities.models import ProtectedCapability

class CustomRegisterApplicationForm(ModelForm):
    def __init__(self, user, *args, **kwargs):
         super(CustomRegisterApplicationForm, self).__init__(*args, **kwargs)
         choices = []
         groups = user.groups.values_list('id',flat=True)
         for g in groups:
            pcs = ProtectedCapability.objects.filter(group=g)
            for i in pcs:
                choices.append([i.pk , i.title])
         self.fields['scope'].choices = choices
    
    class Meta:
        model = get_application_model()
        fields= ('scope', 'name', 'client_id', 'client_secret', 'client_type',
                 'authorization_grant_type','redirect_uris')
   
    required_css_class = 'required'