#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from . import views
from .views.custom_app_register import RegisterApplication




urlpatterns = (
    url(r'^authorize/$', views.AuthorizationView.as_view(), name="authorize"),
    url(r'^token/$', views.TokenView.as_view(), name="token"),
    url(r'^revoke_token/$', views.RevokeTokenView.as_view(), name="revoke-token"),
)

# Application management views
urlpatterns += (
    url(r'^applications/$', views.ApplicationList.as_view(), name="dote_list"),
    #url(r'^applications/register/$', views.ApplicationRegistration.as_view(), name="dote_register"),
    url(r'^applications/register/$', RegisterApplication, name="dote_register"),
    url(r'^applications/(?P<pk>\d+)/$', views.ApplicationDetail.as_view(), name="dote_detail"),
    url(r'^applications/(?P<pk>\d+)/delete/$', views.ApplicationDelete.as_view(), name="dote_delete"),
    url(r'^applications/(?P<pk>\d+)/update/$', views.ApplicationUpdate.as_view(), name="dote_update"),
)

urlpatterns += (
    url(r'^authorized_tokens/$', views.AuthorizedTokensListView.as_view(), name="dote_authorized-token-list"),
    url(r'^authorized_tokens/(?P<pk>\d+)/delete/$', views.AuthorizedTokenDeleteView.as_view(),
        name="dote_authorized-token-delete"),
    )
