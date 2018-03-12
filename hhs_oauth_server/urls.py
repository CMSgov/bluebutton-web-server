from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from apps.accounts.views.oauth2_profile import openidconnect_userinfo
from apps.fhir.bluebutton.views.home import fhir_conformance
from apps.home.views import home
from hhs_oauth_server.hhs_oauth_server_context import IsAppInstalled

__author__ = "Alan Viars"

admin.autodiscover()

ADMIN_REDIRECTOR = getattr(settings, 'ADMIN_PREPEND_URL', '')

urlpatterns = [
    url(r'.well-known/', include('apps.wellknown.urls')),
    url(r'^v1/accounts/', include('apps.accounts.urls')),
    url(r'^v1/connect/userinfo', openidconnect_userinfo, name='openid_connect_userinfo'),
    url(r'^v1/fhir/metadata$', fhir_conformance, name='fhir_conformance_metadata'),
    url(r'^v1/fhir/', include('apps.fhir.bluebutton.urls')),
    url(r'^v1/o/', include('apps.dot_ext.urls')),
    url(r'^social-auth/', include('social_django.urls', namespace='social')),

    url(r'^' + ADMIN_REDIRECTOR + 'admin/', include(admin.site.urls)),
]

if IsAppInstalled("apps.testclient"):
    urlpatterns += [
        url(r'^testclient/', include('apps.testclient.urls')),
    ]

if IsAppInstalled("apps.mymedicare_cb"):
    urlpatterns += [
        url(r'^mymedicare/', include('apps.mymedicare_cb.urls')),
    ]

if not getattr(settings, 'NO_UI', False):
    urlpatterns += [
        url(r'^$', home, name='home'),
    ]
