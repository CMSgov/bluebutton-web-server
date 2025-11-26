from django.urls import re_path
from django.contrib import admin

from apps.fhir.bluebutton.views.read import (
    ReadViewCoverage,
    ReadViewExplanationOfBenefit,
)
from apps.fhir.bluebutton.views.search import (
    SearchViewCoverage,
    SearchViewExplanationOfBenefit,
)
from apps.fhir.bluebutton.views.patient_viewset import PatientViewSet

admin.autodiscover()

urlpatterns = [
    # Patient ReadView
    re_path(
        r'Patient/(?P<resource_id>[^/]+)',
        PatientViewSet.as_view({'get': 'retrieve'}, version=2),
        name='bb_oauth_fhir_patient_read_or_update_or_delete_v2',
    ),
    # Patient SearchView
    re_path(
        r'Patient[/]?',
        PatientViewSet.as_view({'get': 'list'}, version=2),
        name='bb_oauth_fhir_patient_search_v2',
    ),
    # Coverage ReadView
    re_path(
        r"Coverage/(?P<resource_id>[^/]+)",
        ReadViewCoverage.as_view(version=2),
        name="bb_oauth_fhir_coverage_read_or_update_or_delete_v2",
    ),
    # Coverage SearchView
    re_path(
        r"Coverage[/]?",
        SearchViewCoverage.as_view(version=2),
        name="bb_oauth_fhir_coverage_search_v2",
    ),
    # EOB ReadView
    re_path(
        r"ExplanationOfBenefit/(?P<resource_id>[^/]+)",
        ReadViewExplanationOfBenefit.as_view(version=2),
        name="bb_oauth_fhir_eob_read_or_update_or_delete_v2",
    ),
    # EOB SearchView
    re_path(
        r"ExplanationOfBenefit[/]?",
        SearchViewExplanationOfBenefit.as_view(version=2),
        name="bb_oauth_fhir_eob_search_v2",
    ),
]
