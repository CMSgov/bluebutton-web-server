#!/usr/bin/env python
from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import CertifyingBody


class CertifyingBodyForm(forms.ModelForm):
    class Meta:
        model = CertifyingBody
        fields = (  'iss','email','title', 'website_url',       
                    'public_cert_url', 'first_name',  'last_name',         
                    'organization_name')
   
    required_css_class = 'required'
