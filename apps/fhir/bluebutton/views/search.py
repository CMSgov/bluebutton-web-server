import logging

from django.views.decorators.csrf import csrf_exempt

from apps.fhir.fhir_core.utils import kickout_400
from apps.fhir.bluebutton.views.read import generic_read
from apps.fhir.bluebutton.views.home import (fhir_conformance,
                                             fhir_search_home)

logger = logging.getLogger('hhs_server.%s' % __name__)
logger_error = logging.getLogger('hhs_server_error.%s' % __name__)
logger_debug = logging.getLogger('hhs_server_debug.%s' % __name__)
logger_info = logging.getLogger('hhs_server_info.%s' % __name__)

DF_EXTRA_INFO = False


@csrf_exempt
def search_simple(request, resource_type):
    """Route to search FHIR Interaction"""

    if request.method == 'GET':
        # Search
        logger.debug("searching with Resource:"
                     "%s and Id:%s" % (resource_type, id))
        return generic_read(request, resource_type, id)
    # elif request.method == 'PUT':
    #     # update
    #     return update(request, resource_type, id)
    # elif request.method == 'DELETE':
    #     # delete
    #     return delete(request, resource_type, id)
    # else:
    # Not supported.
    msg = "HTTP method %s not supported at this URL." % (request.method)
    # logger_info.info(msg)
    logger.debug(msg)

    return kickout_400(msg)


def search(request, resource_type, *args, **kwargs):
    """
    Search from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/
    """

    interaction_type = 'search'

    logger.debug("Received:%s" % resource_type)
    logger_debug.debug("Received:%s" % resource_type)

    conformance = False
    if "_getpages" in request.GET:
        # a request can be made without a resource name
        # if the GET Parameters include _getpages it is asking for the
        # next batch of resources from a previous search
        conformance = False
        logger.debug("We need to get a searchset: %s" % request.GET)

    elif resource_type is None:
        conformance = True
    elif resource_type.lower() == 'metadata':
        # metadata is a valid resourceType to request the
        # Conformance/Capability Statement
        conformance = True
    elif resource_type.lower == 'conformance':
        # Conformance is the Dstu2 name for the list of resources supported
        conformance = True
    elif resource_type.lower == "capability":
        # Capability is the Stu3 name for the list of resources supported
        conformance = True

    if conformance:
        return fhir_conformance(request, resource_type, *args, **kwargs)

    logger.debug("Interaction:%s. "
                 "Calling generic_read for %s" % (interaction_type,
                                                  resource_type))

    logger_debug.debug("Interaction:%s. "
                       "Calling generic_read for %s" % (interaction_type,
                                                        resource_type))

    if "_getpages" in request.GET:
        # Handle the next searchset
        search = fhir_search_home(request)
    else:
        # Otherwise we should have a resource_type and can perform a search
        search = generic_read(request,
                              interaction_type,
                              resource_type,
                              id,
                              *args,
                              **kwargs)
    return search
