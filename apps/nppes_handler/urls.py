#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from .views import *


urlpatterns = [
    # NPPES Update --------------------------------------
    url(r'^update', nppes_update, name="nppes_update"),
    ]
