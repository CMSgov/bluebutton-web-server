from django.conf.urls import url
from django.contrib import admin

from apps.fhir.bluebutton.views.history import history
from apps.fhir.bluebutton.views.route_rud import read_or_update_or_delete
from apps.fhir.bluebutton.views.vread import vread
from apps.fhir.bluebutton.views.search import search
from apps.fhir.bluebutton.views.home import fhir_conformance

admin.autodiscover()

urlpatterns = [
    # URLs with no authentication
    # Interactions on Resources

    # Move Conformance and Capability above general calls
    # Conformance statement
    url(r'^metadata[^/]',
        fhir_conformance,
        name='bb_fhir_conformance'),

    # Capability statement
    url(r'^meta[^/]',
        fhir_conformance,
        name='bb_fhir_conformance'),

    # Vread GET --------------------------------
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)/_history/(?P<vid>[^/]+)',
        vread,
        name='bb_fhir_vread'),

    # History GET ------------------------------
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)/_history',
        history,
        name='bb_fhir_history'),

    # ---------------------------------------
    # Read GET
    # Update PUT
    # Delete DELETE
    # ---------------------------------------
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)',
        read_or_update_or_delete,
        name='bb_fhir_read_or_update_or_delete'),

    # Search  GET ------------------------------
    url(r'(?P<resource_type>[^/]+)?', search,
        name='bb_fhir_search'),

]
