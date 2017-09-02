from django.conf.urls import url
from django.contrib import admin

from apps.fhir.bluebutton.views.history import oauth_history
from apps.fhir.bluebutton.views.oauth import oauth_read_or_update_or_delete
from apps.fhir.bluebutton.views.vread import oauth_vread
from apps.fhir.bluebutton.views.search import oauth_search
from apps.fhir.bluebutton.views.home import oauth_fhir_conformance
# from apps.fhir.bluebutton.views.help import bluebutton_help

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

    # ---------------------------------------
    # Read GET
    # Update PUT
    # Delete DELETE
    # ---------------------------------------
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)',
        oauth_read_or_update_or_delete,
        name='bb_oauth_fhir_read_or_update_or_delete'),

    # Search  GET ------------------------------
    url(r'(?P<resource_type>[^/]+)?',
        oauth_search,
        name='bb_oauth_fhir_search'),

    # Conformance statement
    url(r'(metadata[^/]+)?',
        oauth_fhir_conformance,
        name='bb_oauth_fhir_conformance'),

    # Capability statement
    url(r'(meta[^/]+)?',
        oauth_fhir_conformance,
        name='bb_oauth_fhir_conformance'),
]
