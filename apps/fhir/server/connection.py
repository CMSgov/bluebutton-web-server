from apps.fhir.bluebutton.utils import (
    generate_info_headers,
    set_default_header,
)


def headers(request, url=None):
    header_info = generate_info_headers(request)

    header_info = set_default_header(request, header_info)

    header_info['BlueButton-OriginalUrl'] = request.path
    header_info['BlueButton-OriginalQuery'] = request.META['QUERY_STRING']
    header_info['BlueButton-BackendCall'] = url
    return header_info
