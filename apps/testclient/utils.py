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
    host = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')
    if not (host.startswith("http://") or host.startswith("https://")):
        host = "https://" + host
    response['resource_uri'] = host
    response['redirect_uri'] = '%s/testclient/callback' % host
    response['authorization_uri'] = '%s/o/authorize/' % host
    response['token_uri'] = '%s/o/token/' % host
    response['userinfo_uri'] = '%s/connect/userinfo' % host
    response['patient_uri'] = '%s/protected/bluebutton/fhir/v1/Patient/' % host
    response['eob_uri'] = '%s/protected/bluebutton/fhir/v1/ExplanationOfBenefit/' % host
    response['coverage_uri'] = '%s/protected/bluebutton/fhir/v1/Coverage/' % host
    return(response)
