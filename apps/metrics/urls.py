from django.conf.urls import url
from django.contrib import admin
from .views import BeneMetricsView

admin.autodiscover()

urlpatterns = [
    url(r'^beneficiaries$', BeneMetricsView.as_view(), name='beneficiaries'),
]
