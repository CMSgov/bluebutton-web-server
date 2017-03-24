# import ast
# import json
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
        # jdecode = json.decoder.JSONDecoder()
        # list_out = ast.literal_eval(t_in)
        if t_in:
            list_out = eval('t_in')
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

    else:
        new_text_list = [replace_with, ]
        return(list_to_text(new_text_list))
