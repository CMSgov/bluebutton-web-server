from apps.fhir.bluebutton.utils import (build_rewrite_list,
                                        get_host_url,
                                        post_process_request,
                                        get_response_text)


def localize(request=None,
             response=None,
             crosswalk=None,
             resource_type=None):

    rewrite_list = build_rewrite_list(crosswalk)

    host_path = get_host_url(request, resource_type)[:-1]

    text_in = get_response_text(fhir_response=response)

    return post_process_request(request,
                                host_path,
                                text_in,
                                rewrite_list)
