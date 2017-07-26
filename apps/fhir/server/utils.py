import re
import logging

logger = logging.getLogger('hhs_server.%s' % __name__)
logger_error = logging.getLogger('hhs_server_error.%s' % __name__)
logger_debug = logging.getLogger('hhs_server_debug.%s' % __name__)
logger_info = logging.getLogger('hhs_server_info.%s' % __name__)


def text_to_list(t_in='[]'):
    """
    Receive object. Convert to list and return
    :param t_in:
    :return: list_out

    """
    logger.debug("text_to_list %s[%s]" % (t_in, type(t_in)))
    if type(t_in) is list:
        return(t_in)
    else:
        logger.debug("decoding with text_to_list %s[%s]" % (t_in, type(t_in)))
        if t_in:
            # list_out = eval('t_in')
            # replace eval with re.compile to convert text to list.
            # first build a list of delimiters to remove ( [ " ' space ] )
            strip_out = re.compile('[["\' \]]')
            # now we evaluate the string list and split on commas
            list_out = strip_out.sub('', t_in).split(',')
        else:
            list_out = []
        logger.debug("decoded with json.decoder %s[%s]" % (list_out,
                                                           type(list_out)))
        return list_out


def list_to_text(l_in=[]):
    """
    Receive list, convert to text and return
    :type l_in: object
    :type l_in:list
    """

    logger.debug("list_to_text %s[%s]" % (l_in, type(l_in)))

    return repr(l_in)


def add_to_text_list(t_list='[]', add_this=''):
    """
    Receive a list as text, convert to list, add item to list
    new_list as text

    :param t_list:
    :param add_this:
    :return: list_to_text(appended_list)
    """

    logger.debug("add_to_text_list %s[%s] + %s[%s]" % (t_list,
                                                       type(t_list),
                                                       add_this,
                                                       type(add_this)))

    appended_list = text_to_list(t_list)
    if add_this:
        appended_list.append(add_this)

    return(list_to_text(appended_list))


def init_text_list(replace_with=''):
    """
    Create a list in text format using replace_with
    Use replace_with if type list otherwise
    create list and add replace_with

    :param replace_with:
    :return: new_text_list

    """

    logger.debug("init_text_list %s[%s] " % (replace_with,
                                             type(replace_with)))

    if type(replace_with) is list:
        return(list_to_text(replace_with))

    new_text_list = [replace_with, ]
    return (list_to_text(new_text_list))


def eval_format_type(format_defn=None):
    """
    Evaluate the content of _format and return 'json' (default)
    or 'xml' | 'html'
    :param format_defn: the value of _format url parameter
    :return: format_type

                xml	                    json
    Resource	application/xml+fhir	application/json+fhir
    Bundle	    application/atom+xml	application/json+fhir
    TagList	    application/xml+fhir	application/json+fhir

    """

    json_type = 'json'
    xml_type = 'xml'
    atom_type = 'xml'
    html_type = 'html'

    if format_defn is None:
        return json_type

    if 'json' in format_defn.lower():
        return json_type
    elif 'xml' in format_defn.lower():
        return xml_type
    elif 'atom' in format_defn.lower():
        return atom_type
    elif 'html' in format_defn.lower():
        return html_type
    else:
        # not sure what was requested so we will report it and default to json
        logger.error('_format request is unknown:%s' % format_defn)
        return json_type

    # catch all
    return json_type


def save_request_format(input_parameters):
    """

    :param input_parameters:
    :return:
    """

    if "_format" in input_parameters:
        return input_parameters['_format']

    return None


def set_fhir_format(fmt_type):
    """
    Get the fmt_type: json|xml|html
    convert to propoer fhir _format
    :param fmt_type:
    :return:

                    xml	                    json
    Resource	application/xml+fhir	application/json+fhir
    Bundle	    application/atom+xml	application/json+fhir
    TagList	    application/xml+fhir	application/json+fhir

    """

    fhir_json = 'application/json+fhir'
    fhir_xml = 'application/xml+fhir'
    fhir_atom = 'application/atom+xml'
    fhir_html = 'application/json+fhir'

    if fmt_type.lower() is 'json':
        return fhir_json
    elif fmt_type.lower() is 'xml':
        return fhir_xml
    elif fmt_type.lower() is 'html':
        return fhir_html
    elif fmt_type.lower() is 'atom':
        return fhir_atom
    else:
        # not sure what was requested so we will report it and default to json
        logger.error('fmt_type is unknown:%s' % fmt_type)
    return fhir_json


def set_resource_id(srtc, resource_id, patient_id):
    """
    if resourceType is Patient we need to replace resource_id with patient_id
    from crosswalk
    if otherwise we need to remove the resource_id from url and
    add _id = resource_id

    setup dict to return this information

    :return: id_dict
    """

    id_dict = {}

    if srtc.resourceType.lower() is 'patient':
        id_dict['query_mode'] = 'read'
        id_dict['url_id'] = patient_id
        id_dict['_id'] = resource_id
        id_dict['patient'] = ''

    else:

        id_dict['query_mode'] = 'search'
        id_dict['url_id'] = ''
        id_dict['_id'] = resource_id
        id_dict['patient'] = patient_id

    return id_dict


def payload_additions(payload=None, list_to_add=None):
    """
    add list_to_add to payload dict
    :param payload:
    :param list_to_add:
    :return:
    """

    if payload is None:
        payload = {}

    if list_to_add is None:
        return payload

    # process the additions
    for k, v in list_to_add.items():
        payload[k] = v

    return payload


def search_add_to_list(srtc_search_add):
    """
    Convert the text in srtc.search_add
    split on , then on =

    :param srtc:
    :return:
    """

    params = {}
    k_v = []
    if srtc_search_add:

        for item in srtc_search_add.split(','):
            k_v.append(item)

        for k in k_v:
            if "=" in k:
                key_value = k.split('=')
                if key_value[0]:
                    params[key_value[0]] = key_value[1]

    return params


def payload_var_replace(payload={}, key=None, new_value=None, old_value=None):
    """
    replace the content of key if old_value with new_value.
    Return payload
    :param payload:
    :param key:
    :param old_value:
    :param new_value:
    :return:
    """

    if len(payload) == 0:
        # no payload received
        return

    if key is None:
        return payload

    if old_value is not None:
        # does the old_value appear in payload['key']

        if key in payload:
            if payload[key] == old_value:
                # match so replace old with new
                if new_value is None:
                    del payload[key]
                else:
                    payload[key] = new_value
            elif old_value in payload[key]:
                payload[key] = payload[key].replace(old_value, new_value)

    else:
        if new_value is None:
            if key in payload:
                del payload[key]
        else:
            payload[key] = new_value

    return payload
