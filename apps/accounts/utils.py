#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings
import json
from django.contrib.auth import login, authenticate
from django.http import HttpResponse




def verify(verification_key):
    if SHA1_RE.search(verification_key):
        try:
            profile = RegistrationProfile.objects.get(activation_key=verification_key)
        except RegistrationProfile.DoesNotExist:
            return False
        if not profile.activation_key_expired():
            user = profile.user
            user.save()
            profile.activation_key = 'EMAIL_VERIFIED'
            profile.save()
            return user
    return False

