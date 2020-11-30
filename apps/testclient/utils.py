from collections import OrderedDict
from django.conf import settings
from ..dot_ext.models import Application


def test_setup(bfd_ver='v1', include_client_secret=True):

    response = OrderedDict()
    oa2client = Application.objects.get(name="TestApp")
    response['client_id'] = oa2client.client_id
    if include_client_secret:
        response['client_secret'] = oa2client.client_secret
    host = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')
    if not (host.startswith("http://") or host.startswith("https://")):
        host = "https://" + host
    response['resource_uri'] = host
    response['redirect_uri'] = '%s/testclient/callback' % host
    response['authorization_uri'] = '%s/%s/o/authorize/' % (host, bfd_ver)
    response['token_uri'] = '%s/%s/o/token/' % (host, bfd_ver)
    response['userinfo_uri'] = '%s/%s/connect/userinfo' % (host, bfd_ver)
    response['patient_uri'] = '%s/%s/fhir/Patient/' % (host, bfd_ver)
    response['eob_uri'] = '%s/%s/fhir/ExplanationOfBenefit/' % (host, bfd_ver)
    response['coverage_uri'] = '%s/%s/fhir/Coverage/' % (host, bfd_ver)
    return(response)


def get_client_secret():
    oa2client = Application.objects.get(name="TestApp")
    return oa2client.client_secret
