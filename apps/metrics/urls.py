from django.conf.urls import url
from django.contrib import admin
from .views import (
    BeneMetricsView,
    AppMetricsView,
    AppMetricsDetailView,
    TokenMetricsView,
    DevelopersView,
)

admin.autodiscover()

urlpatterns = [
    url(r'^beneficiaries$', BeneMetricsView.as_view(), name='beneficiaries'),
    url(r'^applications/(?P<pk>\d+)$', AppMetricsDetailView.as_view(), name='applications-detail'),
    url(r'^applications/$', AppMetricsView.as_view(), name='applications'),
    url(r'^developers/$', DevelopersView.as_view(), name='developers'),
    url(r'^tokens$', TokenMetricsView.as_view(), name='tokens'),
]
