from django.conf.urls import url
from django.contrib import admin
from .views import AuthenticatedHomeView, HomeView

admin.autodiscover()

urlpatterns = [
    url(r'home', AuthenticatedHomeView.as_view(), name='auth_home'),
    url(r'', HomeView.as_view(), name='auth_home'),
]
