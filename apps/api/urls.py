from django.conf.urls import url

from .views import api_read, api_write


urlpatterns = [
    # Read -----------------------------------
    url(r'^read/$', api_read, name='api_read'),

    # Write-----------------------------------
    url(r'^write/$', api_write, name='api_write'),
]
