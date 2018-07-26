from django.conf.urls import url
from .views import Check

urlpatterns = [
    url(r'', Check.as_view()),
]
