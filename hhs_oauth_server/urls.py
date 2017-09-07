#!/usr/bin/env python
from decorate_url import decorated_url
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from apps.accounts.views.oauth2_profile import (openidconnect_userinfo,
                                                userinfo_w_login)
from apps.dot_ext.views.dcrp import register
from apps.fhir.bluebutton.views.home import fhir_search_home
from hhs_oauth_server.hhs_oauth_server_context import IsAppInstalled
admin.autodiscover()

ADMIN_REDIRECTOR = getattr(settings, 'ADMIN_PREPEND_URL', '')

urlpatterns = [
    url(r'^accounts/', include('apps.accounts.urls')),
    url(r'^connect/userinfo', openidconnect_userinfo,
        name='openid_connect_userinfo'),
    url(r'^userinfo', userinfo_w_login,
        name='openid_connect_user_w_login'),
    url(r'^register', register, name='dcrp_register'),
    url(r'.well-known/', include('apps.wellknown.urls')),
    url(r'^consent/', include('apps.fhir.fhir_consent.urls')),
    url(r'^education/', include('apps.education.urls')),
    url(r'^api/', include('apps.api.urls')),
    url(r'^fhir/v3/', include('apps.fhir.server.urls')),
    url(r'^protected/bluebutton/fhir/v1/', include('apps.fhir.bluebutton.urls_oauth')),
    url(r'^bluebutton/fhir/v1/', include('apps.fhir.bluebutton.urls')),
    url(r'^capabilities/', include('apps.capabilities.urls')),
    url(r'^endorsements/', include('apps.dot_ext.endorsementurls')),
    url(r'^home/', include('apps.home.urls')),
    url(r'^o/', include('apps.dot_ext.urls')),
    url(r'^social-auth/', include('social_django.urls', namespace='social')),
    # Admin
    url(r'^admin/', include(admin.site.urls)),

    decorated_url(r'^' + ADMIN_REDIRECTOR + 'admin/', include(admin.site.urls),
                  wrap=staff_member_required(login_url=settings.LOGIN_URL)),
]

if IsAppInstalled("apps.extapi"):
    urlpatterns += [
        url(r'^extapi/', include('apps.extapi.urls')),
    ]

urlpatterns += [
    # Catch all
    url(r'^$', fhir_search_home, name='home'),
]
