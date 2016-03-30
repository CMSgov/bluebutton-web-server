#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url

from .views.create import create
from .views.rud import read_or_update_or_delete
from .views.search import search
from .views.history import history, vread
from .views.hello import hello
from .views.oauth import oauth_create, oauth_read_or_update_or_delete


urlpatterns = [   
    
    #Hello
    url(r'hello', hello,
        name='fhir_hello'),

    # oAuth2 URLs ------------------------------------
    
    # ---------------------------------------
    # Read GET
    # Update PUT
    # Delete DELETE
    # ---------------------------------------
    url(r'oauth2/(?P<resource_type>[^/]+)/(?P<id>[^/]+)',
        oauth_read_or_update_or_delete,
        name='fhir_oauth_read_or_update_or_delete'),
    
    #create ------------------------------
    url(r'oauth2/(?P<resource_type>[^/]+)', oauth_create,
        name='fhir_oauth_create'),
    
    
    # #update
    # url(r'oauth2/(?P<resource_type>[^/]+)/(?P<id>[^/]+)',
    #     oauth_update,
    #     name='fhir_oauth_update'),
    # 
    
    
    #URLs with no authentication
    #Interactions on Resources
    #Vread GET --------------------------------
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)/_history/(?P<vid>[^/]+)', vread,
        name='fhir_vread'),

    #History GET ------------------------------
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)/_history', history,
        name='fhir_history'),
    
    # ---------------------------------------
    # Read GET
    # Update PUT
    # Delete DELETE
    # ---------------------------------------
    url(r'(?P<resource_type>[^/]+)/(?P<id>[^/]+)',
        read_or_update_or_delete,
        name='fhir_read_or_update_or_delete'),
    
    

    #Create  POST ------------------------------
    url(r'(?P<resource_type>[^/]+)', create,
        name='fhir_create'),
    
    
    #Search  GET ------------------------------
    url(r'(?P<resource_type>[^/]+)?', search,
        name='fhir_search'),
    

    ]
