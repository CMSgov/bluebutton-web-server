#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from .views import learn_0, learn_1, learn_2


urlpatterns = [

    url(r'^learn/0/$', learn_0, name='learn_0'),
    url(r'^learn/1/$', learn_1, name='learn_1'),
    url(r'^learn/2/$', learn_2, name='learn_2'),

]


