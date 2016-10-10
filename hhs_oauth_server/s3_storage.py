#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: s3_storage
Created: 10/3/16 5:55 PM

File created by: 'Mark Scrimshire @ekivemark'

based on
https://www.caktusgroup.com/blog/2014/11/10/
Using-Amazon-S3-to-store-your-Django-sites-static-and-media-files/

"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


# custom_storages
class StaticStorage(S3Boto3Storage):

    location = settings.STATICFILES_LOCATION

    def _clean_name(self, name):
        return name

    def _normalize_name(self, name):
        if not name.endswith('/'):
            name += "/"

        name += self.location
        return name


# media storages
class MediaStorage(S3Boto3Storage):

    location = settings.MEDIAFILES_LOCATION

    def _clean_name(self, name):
        return name

    def _normalize_name(self, name):
        if not name.endswith('/'):
            name += "/"

        name += self.location
        return name
