from django.conf.urls import url
from .views import openid_configuration, ApplicationListView


urlpatterns = [
    url(r'^openid-configuration$',
        openid_configuration,
        name='openid-configuration'),
    url(r'^applications$', ApplicationListView.as_view(), name='applications-list'),
]
