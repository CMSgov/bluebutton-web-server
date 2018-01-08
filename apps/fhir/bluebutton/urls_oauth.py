from django.conf.urls import url
from django.contrib import admin

from apps.fhir.bluebutton.views.history import oauth_history
from apps.fhir.bluebutton.views.read import oauth_read
from apps.fhir.bluebutton.views.vread import oauth_vread
from apps.fhir.bluebutton.views.search import oauth_search

admin.autodiscover()

urlpatterns = [
    # URLs with no authentication
    # Interactions on Resources


    # Vread GET --------------------------------
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)/_history/(?P<vid>[^/]+)',
        oauth_vread,
        name='bb_oauth_fhir_vread'),

    # History GET ------------------------------
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)/_history',
        oauth_history,
        name='bb_oauth_fhir_history'),

    # Read GET
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)',
        oauth_read,
        name='bb_oauth_fhir_read_or_update_or_delete'),

    # Search  GET ------------------------------
    url(r'(?P<resource_type>[^/]+)?',
        oauth_search,
        name='bb_oauth_fhir_search'),
]
