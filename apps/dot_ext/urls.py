from django.conf.urls import include, url
from . import views

oauth2_provider_urls = ([
    url(r'^applications/register/$', views.ApplicationRegistration.as_view(), name="register"),
    url(r'^applications/(?P<pk>\d+)/update/$', views.ApplicationUpdate.as_view(), name="update"),
    url(r'^authorize/$', views.AuthorizationView.as_view(), name="authorize"),
    url(r'^authorize/(?P<uuid>[\w-]+)/$', views.ApprovalView.as_view(), name="authorize-instance"),
], 'dot_ext')

urlpatterns = [
    url(r'', include(oauth2_provider_urls)),
    url(r'', include('oauth2_provider.urls')),
]
