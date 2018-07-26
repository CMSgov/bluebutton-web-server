from apps.fhir.bluebutton.utils import (
    FhirServerAuth,
    generate_info_headers,
    set_default_header,
)


# return certs
def certs(crosswalk=None):
    auth_state = FhirServerAuth(crosswalk)
    return (auth_state.get('cert_file', None), auth_state.get('key_file', None))


def headers(request, url=None):
    header_info = generate_info_headers(request)

    header_info = set_default_header(request, header_info)

    header_info['BlueButton-OriginalUrl'] = request.path
    header_info['BlueButton-OriginalQuery'] = request.META['QUERY_STRING']
    header_info['BlueButton-BackendCall'] = url
    return header_info
