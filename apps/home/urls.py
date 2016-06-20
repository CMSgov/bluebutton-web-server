from django.conf.urls import url

from .views import authenticated_home


urlpatterns = [
    url(r'', authenticated_home, name='home'),
]
