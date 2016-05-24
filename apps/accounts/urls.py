#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from .views.core import (simple_login, create, account_settings, reissue_api_keys,
                         request_invite, mylogout, forgot_password,
                         password_reset_email_verify,  display_api_keys,
                         send_activation_key_via_email, activation_verify)

urlpatterns = [
   
    #login and Logout ------------------------------------
    url(r'login', simple_login,  name="login"),
    url(r'logout$', mylogout, name='mylogout'),
    
    #create and update account info -----------------------
    url(r'create', create,  name="accounts_create"),
    url(r'settings$', account_settings, name='account_settings'),
    
    #Request an invite to signup ---------------------------
    url(r'request-invite', request_invite, name="request_invite"),
    
    #Forgot password? ---------------------------------------
    url(r'forgot-password$', forgot_password, name='forgot_password'),

    #Change password using reset token ------------------------
    url(r'password-reset-email-verify/(?P<reset_password_key>[^/]+)/', password_reset_email_verify,
        name='password_reset_email_verify'),

    #Verify the account
    url(r'activation-verify/(?P<activation_key>[^/]+)/', activation_verify,
        name='activation_verify'),
    
    url(r'display-api-keys$', display_api_keys, name='display_api_keys'),

    url(r'reissue-api-keys$', reissue_api_keys, name='reissue_api_keys'),
]
