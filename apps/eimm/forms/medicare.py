#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: medicare
Created: 7/1/16 11:55 AM


"""
from django import forms

__author__ = 'Mark Scrimshire:@ekivemark'


class Medicare_Connect(forms.Form):
    # Get MyMedicare.gov credentials

    mmg_user = forms.CharField(max_length=250,
                               label="MyMedicare.gov Username:")
    mmg_pwd = forms.CharField(widget=forms.widgets.PasswordInput,
                              label="MyMedicare.gov Password:")
