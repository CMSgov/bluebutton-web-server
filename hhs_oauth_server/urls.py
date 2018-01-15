from decorate_url import decorated_url
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from apps.accounts.views.oauth2_profile import (openidconnect_userinfo,
                                                userinfo_w_login)
from apps.fhir.bluebutton.views.home import fhir_conformance
from apps.home.views import home
from hhs_oauth_server.hhs_oauth_server_context import IsAppInstalled

__author__ = "Alan Viars"

admin.autodiscover()

ADMIN_REDIRECTOR = getattr(settings, 'ADMIN_PREPEND_URL', '')

urlpatterns = [
    url(r'^accounts/', include('apps.accounts.urls')),
    url(r'^connect/userinfo', openidconnect_userinfo,
        name='openid_connect_userinfo'),
    url(r'^userinfo', userinfo_w_login,
        name='openid_connect_user_w_login'),
    url(r'.well-known/', include('apps.wellknown.urls')),
    url(r'^v1/fhir/metadata$',
        fhir_conformance, name='fhir_conformance_metadata'),
    url(r'^v1/fhir/',
        include('apps.fhir.bluebutton.urls_oauth')),
    url(r'^o/', include('apps.dot_ext.urls')),

    url(r'^social-auth/', include('social_django.urls', namespace='social')),

    decorated_url(r'^' + ADMIN_REDIRECTOR + 'admin/', include(admin.site.urls),
                  wrap=staff_member_required(login_url=settings.LOGIN_URL)),
]

if IsAppInstalled("apps.testclient"):
    urlpatterns += [
        url(r'^testclient/', include('apps.testclient.urls')),
    ]

if IsAppInstalled("apps.mymedicare_cb"):
    urlpatterns += [
        url(r'^mymedicare/', include('apps.mymedicare_cb.urls')),
    ]

urlpatterns += [
    # Catch all
    url(r'^$', home, name='home'),
]
