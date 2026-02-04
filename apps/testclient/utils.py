import base64
import hashlib
import secrets
import string

from collections import OrderedDict
from django.conf import settings
from urllib.parse import parse_qs, urlparse
from apps.versions import Versions

from ..dot_ext.models import Application


def _start_url_with_http_or_https(host: str) -> str:
    """Makes sure a URL starts with HTTPS

    This is not comprehensive. It is a light refactoring of old code.
    It tries to make sure that a host starts with HTTP or HTTPS.

    Args:
        host: string
    Returns:
        host: string (with "https://")
    """
    if host.startswith("https://"):
        # This is fine.
        pass
    elif host.startswith("http://"):
        # This is also fine
        pass
    else:
        host = f'https://{host}'  # noqa: E231

    return host


def testclient_http_response_setup(include_client_secret: bool = True, version: int = Versions.NOT_AN_API_VERSION) -> OrderedDict:
    """Prepare testclient response environment

    When navigating through the testclient, we need to update the Django session
    so that the authorization process can complete. This function builds a dictionary
    that is used to extend the Django session. It is also used in several unit tests for
    a similar purpose.

    Args:
        include_client_secret (bool) : What it says.
        version (Version): Which version of the API are we navigating through.

    Returns:
        OrderedDict: A dictionary used to prepare/extend the Django session.
    """
    response = OrderedDict()

    response['api_ver'] = version

    oa2client = Application.objects.get(name="TestApp")
    response['client_id'] = oa2client.client_id

    if include_client_secret:
        response['client_secret'] = oa2client.client_secret

    host = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')
    host = _start_url_with_http_or_https(host)

    response['resource_uri'] = host
    response['redirect_uri'] = '{}{}'.format(host, settings.TESTCLIENT_REDIRECT_URI)
    response['coverage_uri'] = '{}/v{}/fhir/Coverage/'.format(host, version)

    auth_data = __generate_auth_data()
    response['code_challenge_method'] = "S256"
    response['code_verifier'] = auth_data['code_verifier']
    response['code_challenge'] = auth_data['code_challenge']
    response['state'] = auth_data['state']

    response['authorization_uri'] = f'{host}/v{version}/o/authorize/'
    response['token_uri'] = f'{host}/v{version}/o/token/'
    response['userinfo_uri'] = f'{host}/v{version}/connect/userinfo'
    response['patient_uri'] = f'{host}/v{version}/fhir/Patient/'
    response['eob_uri'] = f'{host}/v{version}/fhir/ExplanationOfBenefit/'
    response['coverage_uri'] = f'{host}/v{version}/fhir/Coverage/'
    response['digital_insurance_card_uri'] = f'{host}/v{version}/fhir/Patient/$generate-insurance-card/'

    return response


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
    result = ''.join(secrets.choice(letters) for i in range(length))
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
    auth_data = {"state": __generate_random_state(512)}
    auth_data.update(__generate_pkce_data())
    return auth_data


def _ormap(fun, ls):
    """True if `fun` returns true for any element of the list.

    See https://stackoverflow.com/questions/35784074/does-python-have-andmap-ormap.

    Args:
        fun (any -> boolean): Function of one argument; takes any value and returns a boolean
        ls (list): A list of elements of any type

    Returns:
        bool: True if `fun` returned true when applied to any element of the list.
    """
    return any(map(fun, ls))


def _deepfind(obj, val: str):
    """Looks for a value anywhere in a datastructure.

    Args:
        obj (iterable | any): The object we want to search
        val (str): The string we want to search for.

    Returns:
        bool: true if the string is found as a subset of any string or iterable
            within the data structure.
    """
    if isinstance(obj, str):
        # If we are looking at a string, ask if the value we are looking for is
        # equal to or a substring of the string in question.
        return val in obj
    elif isinstance(obj, list):
        # If we are looking at a list, then we should return true if _deepfind on
        # any of the elements of the list returns true.
        return _ormap(lambda o: _deepfind(o, val), obj)
    elif isinstance(obj, dict):
        # If we have a k/v dictionary, then we return true if _deepfind on
        # any of the values in the dict returns true.
        return _ormap(lambda o: _deepfind(o, val), obj.values())
    else:
        # We return false in all other cases. This guarantees termination.
        return False
