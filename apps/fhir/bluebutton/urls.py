from django.conf.urls import url
from django.contrib import admin

from apps.fhir.bluebutton.views.read import ReadViewCoverage, ReadViewExplanationOfBenefit, ReadViewPatient
from apps.fhir.bluebutton.views.search import SearchViewCoverage, SearchViewExplanationOfBenefit, SearchViewPatient

admin.autodiscover()

urlpatterns = [
    # Patient ReadView
    url(r'Patient/(?P<resource_id>[^/]+)',
        ReadViewPatient.as_view(),
        name='bb_oauth_fhir_patient_read_or_update_or_delete'),

    # Patient SearchView
    url(r'Patient[/]?',
        SearchViewPatient.as_view(),
        name='bb_oauth_fhir_patient_search'),

    # Coverage ReadView
    url(r'Coverage/(?P<resource_id>[^/]+)',
        ReadViewCoverage.as_view(),
        name='bb_oauth_fhir_coverage_read_or_update_or_delete'),

    # Coverage SearchView
    url(r'Coverage[/]?',
        SearchViewCoverage.as_view(),
        name='bb_oauth_fhir_coverage_search'),

    # EOB ReadView
    url(r'ExplanationOfBenefit/(?P<resource_id>[^/]+)',
        ReadViewExplanationOfBenefit.as_view(),
        name='bb_oauth_fhir_eob_read_or_update_or_delete'),

    # EOB SearchView
    url(r'ExplanationOfBenefit[/]?',
        SearchViewExplanationOfBenefit.as_view(),
        name='bb_oauth_fhir_eob_search'),
]
