from django.conf.urls import url
from django.contrib import admin

from apps.fhir.bluebutton.views.read import oauth_read
from apps.fhir.bluebutton.views.search import oauth_search

admin.autodiscover()

urlpatterns = [
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)',
        oauth_read,
        name='bb_oauth_fhir_read_or_update_or_delete'),

    url(r'(?P<resource_type>[^/]+)',
        oauth_search,
        name='bb_oauth_fhir_search'),
]
