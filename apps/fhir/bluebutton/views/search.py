import logging


from apps.fhir.bluebutton.views.read import generic_read


logger = logging.getLogger('hhs_server.%s' % __name__)


DF_EXTRA_INFO = False


@csrf_exempt
def search_simple(request, resource_type):
    """Route to search FHIR Interaction"""

    if request.method == 'GET':
        # Search
        return read(request, resource_type, id)
    # elif request.method == 'PUT':
    #     # update
    #     return update(request, resource_type, id)
    # elif request.method == 'DELETE':
    #     # delete
    #     return delete(request, resource_type, id)
    # else:
    # Not supported.
    msg = "HTTP method %s not supported at this URL." % (request.method)
    return kickout_400(msg)


def search(request, resource_type, *args, **kwargs):
    """
    Search from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/
    """

    interaction_type = 'search'
    logger.debug("Interaction:%s. Calling generic_read")
    search = generic_read(request, interaction_type, resource_type, id, *args, **kwargs)
    return search
