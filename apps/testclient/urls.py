from django.conf.urls import url
from .views import (authorize_link, callback, test_eob, test_userinfo,
                    test_coverage, test_patient, test_links)


urlpatterns = [

    url(r'^callback$', callback, name='testclient-callback'),
    url(r'^authorize-link$', authorize_link, name='authorize_link'),
    url(r'^$', test_links, name='test_links'),
    url(r'^ExplanationOfBenefit$', test_eob, name='test_eob'),
    url(r'^Patient$', test_patient, name='test_patient'),
    url(r'^Coverage$', test_coverage, name='test_coverage'),
    url(r'^userinfo$', test_userinfo, name='test_userinfo'),
]
