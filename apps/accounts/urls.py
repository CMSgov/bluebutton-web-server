#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from .views.views import *
from .views.learn import (learn_0,
                          learn_1,
                          learn_2)


urlpatterns = [

    url(r'login', simple_login,  name="login"),
    url(r'create', create,  name="accounts_create"),
    url(r'request-invite', request_invite,  name="accounts_request_invite"),
    url(r'logout$', mylogout, name='mylogout'),
    url(r'password-reset-request$', password_reset_request,
        name='password_reset_request'),

    url(r'settings$', account_settings, name='account_settings'),
    url(r'reset-password/(?P<reset_password_key>[^/]+)/', reset_password,
        name='password_reset_request'),

    url(r'signup-verify/(?P<signup_key>[^/]+)/', signup_verify,
        name='signup_verify'),


    url(r'display-api-keys$', display_api_keys,
        name='display_api_keys'),


    url(r'reissue-api-keys$', reissue_api_keys,
        name='reissue_api_keys'),

    url(r'^learn/0/$',
        learn_0,
        name='learn_0'),
    url(r'^learn/1/$',
        learn_1,
        name='learn_1'),
    url(r'^learn/2/$',
        learn_2,
        name='learn_2'),

]

# these are the api endpoints exposed by the accounts application
api_urls = [
    url(r'^profile/$', user_self, name='user_self'),
]
