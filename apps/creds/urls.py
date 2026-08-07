from django.contrib import admin
from django.urls import re_path

from apps.creds.views import CredentialingRequestView

admin.autodiscover()

urlpatterns = [
    re_path(
        r'(?P<prod_cred_req_id>[^/]+)',
        CredentialingRequestView.as_view(),
        name='credentials_request',
    ),
]
