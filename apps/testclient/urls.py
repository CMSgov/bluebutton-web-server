from django.conf.urls import url
from .views import (authorize_link, callback, test_eob, test_userinfo,
                    test_coverage, test_patient, test_links)
from django.views.generic import TemplateView

urlpatterns = [

    url(r'^callback$', callback, name='testclient-callback'),
    url(r'^authorize-link$', authorize_link, name='authorize_link'),
    url(r'^$', test_links, name='test_links'),
    url(r'^ExplanationOfBenefit$', test_eob, name='test_eob'),
    url(r'^Patient$', test_patient, name='test_patient'),
    url(r'^Coverage$', test_coverage, name='test_coverage'),
    url(r'^userinfo$', test_userinfo, name='test_userinfo'),
    url(r'^ExplanationOfBenefitV2$', test_eob, name='test_eob_v2'),
    url(r'^PatientV2$', test_patient, name='test_patient_v2'),
    url(r'^CoverageV2$', test_coverage, name='test_coverage_v2'),
    url(r'^userinfoV2$', test_userinfo, name='test_userinfo_v2'),
    url(r'^error$', TemplateView.as_view(template_name='error.html'), name='testclient_error_page'),
]
