from django.conf.urls import url

from .views import *


urlpatterns = [
    # Read -----------------------------------
    url(r'^read/$', api_read, name='api_read'),

    # Write-----------------------------------
    url(r'^write/$', api_write, name='api_write'),
]
