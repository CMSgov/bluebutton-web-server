import logging

from collections import OrderedDict
from apps.fhir.server.models import SupportedResourceType

logger = logging.getLogger('hhs_server.%s' % __name__)


def strip_format_for_back_end(pass_params):
    updated_parameters = OrderedDict()
    for k in pass_params:
        if k.lower() == "_format":
            pass
        elif k.lower() == "format":
            pass
        else:
            updated_parameters[k] = pass_params[k]

    updated_parameters["_format"] = "json"
    return updated_parameters


def valid_interaction(resource, resource_router):
    """ Create a list of Interactions for the resource
        We need to deal with multiple objects returned or filter by FHIRServer
    """

    interaction_list = []
    try:
        resource_interaction = \
            SupportedResourceType.objects.get(resourceType=resource,
                                              fhir_source=resource_router)
    except SupportedResourceType.DoesNotExist:
        # this is a strange error
        # earlier gets should have found a record
        # otherwise we wouldn't get in to this function
        # so we will return an empty list.
        return interaction_list

    # Now we can build the interaction_list
    if resource_interaction.get:
        interaction_list.append("get")
    if resource_interaction.put:
        interaction_list.append("put")
    if resource_interaction.create:
        interaction_list.append("create")
    if resource_interaction.read:
        interaction_list.append("read")
    if resource_interaction.vread:
        interaction_list.append("vread")
    if resource_interaction.update:
        interaction_list.append("update")
    if resource_interaction.delete:
        interaction_list.append("delete")
    if resource_interaction.search:
        interaction_list.append("search-type")
    if resource_interaction.history:
        interaction_list.append("history-instance")
        interaction_list.append("history-type")

    return interaction_list
