from django.conf.urls import url

from .views import nppes_update


urlpatterns = [
    # NPPES Update --------------------------------------
    url(r'^update', nppes_update, name='nppes_update'),
]
