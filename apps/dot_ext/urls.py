from django.conf.urls import include, url
from . import views
from .views.custom_app_register import RegisterApplication


oauth2_provider_urls = ([
    url(r'^applications/register/$', RegisterApplication, name="register"),
    url(r'^applications/(?P<pk>\d+)/update/$', views.ApplicationUpdate.as_view(), name="update"),
    url(r'', include('oauth2_provider.urls')),
], 'oauth2_provider', 'oauth2_provider')


urlpatterns = [
    url(r'', include(oauth2_provider_urls)),
]
