#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings
from datetime import timedelta, date
from django.db import models
from django.contrib.auth.models import User
from datetime import date, datetime, timedelta
from localflavor.us.models import PhoneNumberField
from localflavor.us.us_states import US_STATES
import string
import random
import uuid
from emails import send_password_reset_url_via_email, send_signup_key_via_email
from django.core.mail import send_mail, EmailMessage
from django.utils.translation import ugettext_lazy as _


USER_CHOICES     = ( ('V','Require-Verification'),
                     ('A','No verification required (attestation)'))

class UserProfile(models.Model):
    user                    = models.OneToOneField(User)
    organization_name       = models.CharField(max_length=256)
    user_type               = models.CharField(default='V',
                                choices=USER_CHOICES,
                                max_length=1)
    access_key_id           = models.CharField(max_length=20, blank=True,)
    access_key_secret       = models.CharField(max_length=40, blank=True, )
    access_key_reset        = models.BooleanField(blank=True, default=False,
                                help_text= _("Check this box to issue a new access key. Doing so invalidates the existing key."))

    def __unicode__(self):
        name = "%s %s" % (self.user.first_name, self.user.last_name)
        return name
    
    def save(self, **kwargs):
        if not self.access_key_id  or self.access_key_reset:
            self.access_key_id = random_key_id()
            self.access_key_secret = random_secret()   
        self.access_key_reset = False
    
        super(UserProfile, self).save(**kwargs)
        

class RequestInvite(models.Model):
    first_name     = models.CharField(max_length = 150)
    last_name      = models.CharField(max_length = 150)
    organization   = models.CharField(max_length = 150)
    email          = models.EmailField(max_length = 150)
    added          = models.DateField(auto_now_add=True)
    def __unicode__(self):
        r = "%s %s" % (self.first_name, self.last_name)
        return r

class Invitation(models.Model):
    code   = models.CharField(max_length = 10, unique=True)
    email  = models.EmailField(blank=True)
    valid = models.BooleanField(default=True)
    added          = models.DateField(auto_now_add=True)
    
    
    def __unicode__(self):
        return self.code
    
    def save(self, **kwargs):
        
         #send the verification email.
        msg = """
        <html>
        <head>
        </head>
        <body>
        Congratulations. You have been invited to join the Enumeration API Alpha.<br>
        
        You may now <a href="%s">register</a>
        with the invitation code: 
        
        <h2>
        %s
        </h2>
        
        - NPPES Modernization Team 
        </body>
        </html>
        """ % (settings.HOSTNAME_URL, self.code,)
        if settings.SEND_EMAIL:
            subj = "[%s] Invitation Code: %s" % (settings.ORGANIZATION_NAME,
                                                    self.code)
            
            msg = EmailMessage(subj, msg, settings.EMAIL_HOST_USER,
                           [self.email, ])            
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send()

        super(Invitation, self).save(**kwargs)
        
class ValidPasswordResetKey(models.Model):
    user               = models.ForeignKey(User)
    reset_password_key = models.CharField(max_length=50, blank=True)
    expires            = models.DateTimeField(default=datetime.now)


    def __unicode__(self):
        return '%s for user %s expires at %s' % (self.reset_password_key,
                                                 self.user.username,
                                                 self.expires)

    def save(self, **kwargs):
         
        self.reset_password_key=str(uuid.uuid4())
        now = datetime.now()
        expires=now+timedelta(minutes=1440)
        self.expires=expires

        #send an email with reset url
        x=send_password_reset_url_via_email(self.user, self.reset_password_key)
        super(ValidPasswordResetKey, self).save(**kwargs)

def random_key_id(y=20):
       return ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for x in range(y))
    
def random_secret(y=40):
       return ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for x in range(y))