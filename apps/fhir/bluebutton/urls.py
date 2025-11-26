from django.urls import re_path
from django.contrib import admin

from apps.fhir.bluebutton.views.read import (
    ReadViewPatient,
    ReadViewCoverage,
    ReadViewExplanationOfBenefit,
)
from apps.fhir.bluebutton.views.search import (
    SearchViewPatient,
    SearchViewCoverage,
    SearchViewExplanationOfBenefit,
)

admin.autodiscover()

urlpatterns = [
    # Patient ReadView
    re_path(
        r"Patient/(?P<resource_id>[^/]+)",
        ReadViewPatient.as_view(),
        name="bb_oauth_fhir_patient_read_or_update_or_delete",
    ),
    # Patient SearchView
    re_path(
        r"Patient[/]?", SearchViewPatient.as_view(), name="bb_oauth_fhir_patient_search"
    ),
    # Coverage ReadView
    re_path(
        r"Coverage/(?P<resource_id>[^/]+)",
        ReadViewCoverage.as_view(),
        name="bb_oauth_fhir_coverage_read_or_update_or_delete",
    ),
    # Coverage SearchView
    re_path(
        r"Coverage[/]?",
        SearchViewCoverage.as_view(),
        name="bb_oauth_fhir_coverage_search",
    ),
    # EOB ReadView
    re_path(
        r"ExplanationOfBenefit/(?P<resource_id>[^/]+)",
        ReadViewExplanationOfBenefit.as_view(),
        name="bb_oauth_fhir_eob_read_or_update_or_delete",
    ),
    # EOB SearchView
    re_path(
        r"ExplanationOfBenefit[/]?",
        SearchViewExplanationOfBenefit.as_view(),
        name="bb_oauth_fhir_eob_search",
    ),
]
