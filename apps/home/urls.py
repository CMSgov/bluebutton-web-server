#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'', authenticated_home, name="home"),
    ]
