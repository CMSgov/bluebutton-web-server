from django.conf.urls import url
from waffle.decorators import waffle_switch
from .views import openid_configuration, ApplicationListView


urlpatterns = [
    url(r'^openid-configuration$',
        openid_configuration,
        name='openid-configuration'),
    url(r'^applications$',
        waffle_switch('wellknown_applications')(ApplicationListView.as_view()),
        name='applications-list'),
]
