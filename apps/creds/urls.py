from django.conf.urls import url
from django.contrib import admin
from apps.creds.views import CredentialingRequestView

admin.autodiscover()

urlpatterns = [
    url(r'(?P<prod_cred_req_id>[^/]+)',
        CredentialingRequestView.as_view(),
        name='credentials_request'),
]
