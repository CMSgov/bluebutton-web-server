from django.conf.urls import url
from django.contrib import admin
from .views import authenticated_home

admin.autodiscover()

urlpatterns = [
    url(r'', authenticated_home, name='auth_home'),
]
