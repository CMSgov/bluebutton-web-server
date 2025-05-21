from django.urls import re_path
from django.contrib import admin
from waffle.decorators import waffle_switch

from apps.fhir.bluebutton.views.read import (
    ReadViewCoverage,
    ReadViewExplanationOfBenefit,
    ReadViewPatient,
)
from apps.fhir.bluebutton.views.search import (
    SearchViewCoverage,
    SearchViewExplanationOfBenefit,
    SearchViewPatient,
)

admin.autodiscover()

urlpatterns = [
    # Patient ReadView
    re_path(
        r"Patient/(?P<resource_id>[^/]+)",
        waffle_switch("v3_endpoints")(ReadViewPatient.as_view(version=3)),
        name="bb_oauth_fhir_patient_read_or_update_or_delete_v3",
    ),
    # Patient SearchView
    re_path(
        r"Patient[/]?",
        waffle_switch("v3_endpoints")(SearchViewPatient.as_view(version=3)),
        name="bb_oauth_fhir_patient_search_v3",
    ),
    # Coverage ReadView
    re_path(
        r"Coverage/(?P<resource_id>[^/]+)",
        waffle_switch("v3_endpoints")(ReadViewCoverage.as_view(version=3)),
        name="bb_oauth_fhir_coverage_read_or_update_or_delete_v3",
    ),
    # Coverage SearchView
    re_path(
        r"Coverage[/]?",
        waffle_switch("v3_endpoints")(SearchViewCoverage.as_view(version=3)),
        name="bb_oauth_fhir_coverage_search_v3",
    ),
    # EOB ReadView
    re_path(
        r"ExplanationOfBenefit/(?P<resource_id>[^/]+)",
        waffle_switch("v3_endpoints")(ReadViewExplanationOfBenefit.as_view(version=3)),
        name="bb_oauth_fhir_eob_read_or_update_or_delete_v3",
    ),
    # EOB SearchView
    re_path(
        r"ExplanationOfBenefit[/]?",
        waffle_switch("v3_endpoints")(SearchViewExplanationOfBenefit.as_view(version=3)),
        name="bb_oauth_fhir_eob_search_v3",
    ),
]
