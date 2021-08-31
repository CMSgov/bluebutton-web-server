from django.conf.urls import url
from .views import openapi

urlpatterns = [
    url(r'^openapi$', openapi, name='bluebutton_openapi'),
]
