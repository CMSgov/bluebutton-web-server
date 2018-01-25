from django.conf.urls import url
from django.contrib import admin

from apps.fhir.bluebutton.views.read import read
from apps.fhir.bluebutton.views.search import search

admin.autodiscover()

urlpatterns = [
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)',
        read,
        name='bb_oauth_fhir_read_or_update_or_delete'),

    url(r'(?P<resource_type>[^/]+)',
        search,
        name='bb_oauth_fhir_search'),
]
