from django.conf.urls import url
from django.contrib import admin
from .views import BeneMetricsView, AppMetricsView, TokenMetricsView

admin.autodiscover()

urlpatterns = [
    url(r'^beneficiaries$', BeneMetricsView.as_view(), name='beneficiaries'),
    url(r'^applications$', AppMetricsView.as_view(), name='applications'),
    url(r'^tokens$', TokenMetricsView.as_view(), name='tokens'),
]
