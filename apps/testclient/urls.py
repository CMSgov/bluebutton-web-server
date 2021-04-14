from django.conf.urls import url
from .views import (authorize_link, authorize_link_v2, restart, callback, test_eob, test_eob_v2,
                    test_userinfo, test_userinfo_v2,
                    test_metadata, test_metadata_v2,
                    test_openid_config, test_openid_config_v2,
                    test_coverage, test_coverage_v2, test_patient, test_patient_v2, test_links)

urlpatterns = [

    url(r'^restart$', restart, name='testclient-restart'),
    url(r'^callback$', callback, name='testclient-callback'),
    url(r'^authorize-link$', authorize_link, name='authorize_link'),
    url(r'^authorize-link-v2$', authorize_link_v2, name='authorize_link_v2'),
    url(r'^$', test_links, name='test_links'),
    url(r'^ExplanationOfBenefit$', test_eob, name='test_eob'),
    url(r'^Patient$', test_patient, name='test_patient'),
    url(r'^Coverage$', test_coverage, name='test_coverage'),
    url(r'^userinfo$', test_userinfo, name='test_userinfo'),
    url(r'^metadata$', test_metadata, name='test_metadata'),
    url(r'^openidConfig$', test_openid_config, name='test_openid_config'),
    url(r'^ExplanationOfBenefitV2$', test_eob_v2, name='test_eob_v2'),
    url(r'^PatientV2$', test_patient_v2, name='test_patient_v2'),
    url(r'^CoverageV2$', test_coverage_v2, name='test_coverage_v2'),
    url(r'^userinfoV2$', test_userinfo_v2, name='test_userinfo_v2'),
    url(r'^metadataV2$', test_metadata_v2, name='test_metadata_v2'),
    url(r'^openidConfigV2$', test_openid_config_v2, name='test_openid_config_v2'),
]
