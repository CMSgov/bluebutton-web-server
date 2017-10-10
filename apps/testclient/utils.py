from __future__ import absolute_import
from __future__ import unicode_literals
from collections import OrderedDict
from django.conf import settings
from ..dot_ext.models import Application

__author__ = "Alan Viars"


def test_setup():

    response = OrderedDict()
    oa2client = Application.objects.get(name="TestApp")
    response['client_id'] = oa2client.client_id
    response['client_secret'] = oa2client.client_secret
    response['resource_uri'] = settings.HOSTNAME_URL
    response['redirect_uri'] = '%s/testclient/callback' % settings.HOSTNAME_URL
    response['authorization_uri'] = '%s/o/authorize/' % settings.HOSTNAME_URL
    response['token_uri'] = '%s/o/token/' % settings.HOSTNAME_URL
    response['userinfo_uri'] = '%s/connect/userinfo' % settings.HOSTNAME_URL
    return(response)
