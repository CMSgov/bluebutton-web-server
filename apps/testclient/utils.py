import base64
import hashlib
import random
import string

from collections import OrderedDict
from django.conf import settings
from urllib.parse import parse_qs, urlparse

from ..dot_ext.models import Application


def test_setup(include_client_secret=True, v2=False, pkce=False):
    response = OrderedDict()
    ver = 'v2' if v2 else 'v1'
    response['api_ver'] = ver
    oa2client = Application.objects.get(name="TestApp")
    response['client_id'] = oa2client.client_id

    if include_client_secret:
        response['client_secret'] = oa2client.client_secret

    host = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')

    if not (host.startswith("http://") or host.startswith("https://")):
        host = "https://" + host

    response['resource_uri'] = host
    response['redirect_uri'] = '{}{}'.format(host, settings.TESTCLIENT_REDIRECT_URI)
    response['coverage_uri'] = '{}/{}/fhir/Coverage/'.format(host, ver)

    if pkce:
        auth_data = __generate_auth_data()
        response['code_challenge_method'] = "S256"
        response['code_verifier'] = auth_data['code_verifier']
        response['code_challenge'] = auth_data['code_challenge']
        response['state'] = auth_data['state']

    response['authorization_uri'] = '{}/{}/o/authorize/'.format(host, ver)
    response['token_uri'] = '{}/{}/o/token/'.format(host, ver)
    response['userinfo_uri'] = '{}/{}/connect/userinfo'.format(host, ver)
    response['patient_uri'] = '{}/{}/fhir/Patient/'.format(host, ver)
    response['eob_uri'] = '{}/{}/fhir/ExplanationOfBenefit/'.format(host, ver)
    response['coverage_uri'] = '{}/{}/fhir/Coverage/'.format(host, ver)
    return (response)


def get_client_secret():
    oa2client = Application.objects.get(name="TestApp")
    return oa2client.client_secret_plain


def extract_page_nav(fhir_json):
    link = fhir_json.get('link', None)
    nav_list = []
    last_link = None
    if link is not None:
        for lnk in link:
            if lnk.get('url', None) is not None and lnk.get('relation', None) is not None:
                if lnk.get('relation') == 'last':
                    last_link = lnk['url']
                nav_list.append({'relation': lnk['relation'], 'nav_link': lnk['url']})
            else:
                nav_list = []
                break
    return nav_list, last_link


def extract_last_page_index(last_url):
    last_pg_ndx = -1
    qparams = parse_qs(urlparse(last_url).query)
    ndx = qparams.get('startIndex', None)
    if ndx and len(ndx) > 0:
        last_pg_ndx = int(ndx[0])
    return last_pg_ndx


def __base64_url_encode(buffer):
    buffer_bytes = base64.urlsafe_b64encode(buffer.encode("utf-8"))
    buffer_result = str(buffer_bytes, "utf-8")
    return buffer_result


def __get_random_string(length) -> str:
    letters = string.ascii_letters + string.digits + string.punctuation
    result = "".join(random.choice(letters) for i in range(length))
    return result


def __generate_pkce_data() -> dict:
    verifier = __generate_random_state(32)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ASCII")).digest()
    )
    return {"code_challenge": code_challenge.decode("utf-8"), "code_verifier": verifier}


def __generate_random_state(num) -> str:
    return __base64_url_encode(__get_random_string(num))


def __generate_auth_data() -> dict:
    auth_data = {"state": __generate_random_state(32)}
    auth_data.update(__generate_pkce_data())
    return auth_data
