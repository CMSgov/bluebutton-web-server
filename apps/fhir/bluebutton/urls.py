from django.conf.urls import url
from django.contrib import admin

from apps.fhir.bluebutton.views.read import ReadView
from apps.fhir.bluebutton.views.search import SearchView

admin.autodiscover()

urlpatterns = [
    url(r'(?P<resource_type>[^/]+)/(?P<resource_id>[^/]+)',
        ReadView.as_view(),
        name='bb_oauth_fhir_read_or_update_or_delete'),

    url(r'(?P<resource_type>[^/]+)',
        SearchView.as_view(),
        name='bb_oauth_fhir_search'),
]
