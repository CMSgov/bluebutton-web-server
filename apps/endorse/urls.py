from django.conf.urls import url

from .views import generate_poet_jwt


urlpatterns = [
    # NPPES Update --------------------------------------
    url(r'^generate-jwt', generate_poet_jwt, name='generate_poet_jwt'),
]
