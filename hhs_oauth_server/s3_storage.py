"""
hhs_oauth_server
FILE: s3_storage
Created: 10/3/16 5:55 PM

File created by: 'Mark Scrimshire @ekivemark'

based on
https://www.caktusgroup.com/blog/2014/11/10/
Using-Amazon-S3-to-store-your-Django-sites-static-and-media-files/

"""
# import logging
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

# logger = logging.getLogger('hhs_server.%s' % __name__)


# custom_storages
class StaticStorage(S3Boto3Storage):

    location = settings.STATICFILES_LOCATION

    def _clean_name(self, name):
        # logger.debug("S3 Storage: Cleaning name:%s" % name)
        return name

    def _normalize_name(self, name):
        # if not name.endswith('/'):
        #     # logger.debug("S3 Storage: Name has no /:%s" % name)
        #     name += "/"

        name = self.location + name
        # logger.debug("S3 Storage: Name with location added: %s" % name)
        return name


# media storages
class MediaStorage(S3Boto3Storage):

    location = settings.MEDIAFILES_LOCATION

    def _clean_name(self, name):
        # logger.debug("S3 Media Storage: Cleaning name:%s" % name)
        return name

    def _normalize_name(self, name):
        # if not name.endswith('/'):
        #     # logger.debug("S3 Media Storage: Name has no /:%s" % name)
        #     name += "/"

        name = self.location + name
        # logger.debug("S3 Media Storage: Name with location added: %s" % name)
        return name
