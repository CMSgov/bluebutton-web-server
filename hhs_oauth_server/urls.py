#!/usr/bin/env python
# from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from apps.accounts.views.oauth2_profile import user_self
from apps.fhir.bluebutton.views.home import fhir_search_home
from hhs_oauth_server.hhs_oauth_server_context import IsAppInstalled
admin.autodiscover()

urlpatterns = [
    url(r'^accounts/', include('apps.accounts.urls')),
    url(r'^consent/', include('apps.fhir.fhir_consent.urls')),
    url(r'^education/', include('apps.education.urls')),
    url(r'^profile/me$', user_self, name='user_self'),
    url(r'^api/', include('apps.api.urls')),
    # url(r'^api/', include(api_urls)),
    url(r'^fhir/v3/', include('apps.fhir.server.urls')),
    url(r'^bluebutton/fhir/v1/', include('apps.fhir.bluebutton.urls')),
    url(r'^capabilities/', include('apps.capabilities.urls')),
    url(r'^endorsements/', include('apps.dot_ext.endorsementurls')),
    url(r'^integration/', include('apps.eimm.urls')),
    url(r'^endorse/', include('apps.endorse.urls')),
    url(r'^home/', include('apps.home.urls')),

    url(r'^o/', include('apps.dot_ext.urls')),
    # url(r'^fhir/api/v1/', include('apps.fhir.bluebutton')),
    # Admin
    url(r'^admin/', include(admin.site.urls)),

]
# if 'apps.fhir.testac' in settings.INSTALLED_APPS:
urlpatterns += [
    url(r'^create_test_account/', include('apps.fhir.testac.urls')),
]

if IsAppInstalled("apps.extapi"):
    urlpatterns += [
        url(r'^extapi/', include('apps.extapi.urls')),
    ]

urlpatterns += [
    # Catch all
    url(r'^', fhir_search_home, name='home'),
]
