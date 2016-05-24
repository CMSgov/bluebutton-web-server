#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from .models import ActivationKey
from datetime import datetime
import pytz


def create_signup_key(user):
    #Create an new activation key and send the email.
    k = ActivationKey.objects.create(user=user)
    return k


def validate_activation_key(activation_key):
    utc=pytz.UTC
    print('here')
    try:
        vc=ActivationKey.objects.get(key=activation_key)
        now=datetime.now().replace(tzinfo=utc)
        expires = vc.expires.replace(tzinfo=utc)
        
        if expires < now:
            vc.delete()
            #The key has expired
            return False   
    except(ActivationKey.DoesNotExist):
        #The key does not exist
        return False  
    #The key exists and has not expired. 
    vc.user.is_active=True
    vc.user.save()
    print(vc.user.is_active)
    
    
    vc.delete()
    return True
