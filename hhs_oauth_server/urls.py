"""sample_oauth_server URL Configuration
"""
from django.conf.urls import include, url
from django.contrib import admin
admin.autodiscover()
from apps.accounts.urls import api_urls

urlpatterns = [
    url(r'^admin/',         include(admin.site.urls)),
    url(r'^accounts/',      include('apps.accounts.urls')),
    url(r'^api/',           include('apps.api.urls')),
    url(r'^api/',           include(api_urls)),
    url(r'^fhir/v3/',       include('apps.fhir.urls')),
    url(r'^nppes/',         include('apps.nppes_handler.urls')),
    url(r'^capabilities/',  include('apps.capabilities.urls')),
    url(r'^o/',             include('apps.dot_ext.urls')),
    url(r'^signups/',       include('apps.signups.urls')),
    url(r'^',               include('apps.home.urls')),
]
