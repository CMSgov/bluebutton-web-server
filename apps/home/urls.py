from django.urls import path, re_path
from django.contrib import admin
from .views import AuthenticatedHomeView, HomeView

admin.autodiscover()

urlpatterns = [
    re_path(r"home", AuthenticatedHomeView.as_view(), name="home"),
    path("", HomeView.as_view(), name="unauth_home"),
]
