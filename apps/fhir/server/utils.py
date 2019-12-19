import re
import logging

logger = logging.getLogger('hhs_server.%s' % __name__)


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
            strip_out = re.compile(r'[["\' \]]')
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
