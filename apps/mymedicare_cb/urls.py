from django.urls import path
from .views import callback, mymedicare_login

urlpatterns = [
    path("sls-callback/<int:version>", callback, name="mymedicare-sls-callback"),
    path("login", mymedicare_login, name="mymedicare-login"),
]
