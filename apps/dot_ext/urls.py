from django.conf.urls import include, url
from ..accounts.decorators import authorize_app_flag_required
from . import views


oauth2_provider_urls = ([
    url(r'^applications/register/$', views.ApplicationRegistration.as_view(), name="register"),
    url(r'^applications/(?P<pk>\d+)/update/$', views.ApplicationUpdate.as_view(), name="update"),
    # url(r'^authorize/$', views.AuthorizationView.as_view(), name="authorize"),
    url(r'^authorize/$', authorize_app_flag_required(views.AuthorizationView.as_view()), name="authorize"),
    url(r'', include('oauth2_provider.urls')),
], 'oauth2_provider', 'oauth2_provider')


urlpatterns = [
    url(r'', include(oauth2_provider_urls)),
]
