from django.urls import re_path
from .views import CheckInternal

urlpatterns = [
    re_path(r"/?$", CheckInternal.as_view()),
]
