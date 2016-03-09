#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from . import views


urlpatterns = (
    url(r'create$', views.create_certifying_body,  name="create_certifying_body"),
    
    url(r'cbjson$', views.certifying_bodies_as_json,  name="certifying_bodies_json"),
    
)

