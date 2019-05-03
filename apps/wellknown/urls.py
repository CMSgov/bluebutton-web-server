from django.conf.urls import url
from waffle.decorators import waffle_switch
from .views import openid_configuration, ApplicationListView, ApplicationLabelView


urlpatterns = [
    url(r'^openid-configuration$',
        openid_configuration,
        name='openid-configuration'),
    url(r'^applications$',
        waffle_switch('wellknown_applications')(ApplicationListView.as_view()),
        name='applications-list'),
    url(r'^application-labels$',
        waffle_switch('wellknown_applications')(ApplicationLabelView.as_view()),
        name='application-labels'),
]
