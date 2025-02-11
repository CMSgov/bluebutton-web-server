from django.urls import path
from .views import callback, mymedicare_login

urlpatterns = [
    path("sls-callback/<str:version>", callback, name="mymedicare-sls-callback_v1"),
    path("sls-callback", callback, name="mymedicare-sls-callback"),
    path("login", mymedicare_login, name="mymedicare-login"),
]
