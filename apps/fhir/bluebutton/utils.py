import json
import logging

try:
    # python2
    from urllib import urlencode
except ImportError:
    # python3
    from urllib.parse import urlencode

from collections import OrderedDict

from django.conf import settings

from apps.fhir.core.utils import (kickout_404, kickout_403)
from apps.fhir.server.models import SupportedResourceType
from apps.fhir.bluebutton.models import ResourceTypeControl

PRETTY_JSON_INDENT = 4

FORMAT_OPTIONS_CHOICES = ['json', 'xml']

logger = logging.getLogger('hhs_server.%s' % __name__)


def notNone(value=None, default=None):
    """
    Test value. Return Default if None
    http://stackoverflow.com/questions/4978738/
    is-there-a-python-equivalent-of-the-c-sharp-null-coalescing-operator
    """
    if value is None:
        return default
    else:
        return value


def strip_oauth(get={}):
    """ Remove OAuth values from URL Parameters being sent to backend """

    # access_token can be passed in as a part of OAuth protected request.
    # as can: state=random_state_string&response_type=code&client_id=ABCDEF
    # Remove them before passing url through to FHIR Server

    if get == {}:
        return get

    strip_parms = ['access_token', 'state', 'response_type', 'client_id']

    # logger.debug('Removing:%s from: %s' % (strip_parms, get))

    strip_oauth = get_url_query_string(get, strip_parms)

    # logger.debug('resulting url parameters:%s' % strip_oauth)

    return strip_oauth


def block_params(get, srtc):
    """ strip parameters from search string - get is a dict """

    # Get parameters
    # split on &
    # get srtc.search_block as list
    if get:
        # set search_params to what is received as a default
        search_params = get
    else:
        # No get parameters to process so return
        search_params = ''
        return search_params

    # Now we need to see if there are any get parameters to remove
    if srtc:
        if srtc.override_search:
            search_params = get_url_query_string(get, srtc.get_search_block())

    # do we need to convert result to json. source could be
    # OrderedDict or string
    # search_params_result = json.dumps(search_params)

    # return search_params_result
    return search_params


def add_params(srtc, key=None):
    """ Add filtering parameters to search string """

    # srtc.get_search_add will return a list
    # this will be in form 'Patient={Value}'
    # Replaceable parameters can be included
    # Currently Supported Replaceable Parameters are:
    # %PATIENT% = key
    # key = FHIR_ID for search parameter. eg. patient= Patient profile Id
    # modify this function to add more Replaceable Parameters

    # Returns List

    # add_params = ''
    add_params = []

    if srtc:
        if srtc.override_search:
            params_list = srtc.get_search_add()

            # logger.debug('Parameters to add:%s' % params_list)

            add_params = []
            for item in params_list:
                # Run through list and do variable replacement
                if '%PATIENT%' in item:
                    if key is None:
                        key_str = ''
                    else:
                        key_str = str(key)
                    item = item.replace('%PATIENT%', key_str)
                    if '%PATIENT%' in item:
                        # Still there we need to remove
                        item = item.replace('%PATIENT%', '')

                add_params.append(item)

            # logger.debug('Resulting additional parameters:%s' % add_params)

    return add_params


def concat_parms(front_part={}, back_part={}):
    """ Concatenate the Query Parameters Strings
        The strings should be urlencoded.

    """

    joined_parms = OrderedDict()

    # logger.debug('Joining %s with: %s' % (front_part, back_part))
    if len(front_part) > 0:
        if isinstance(front_part, dict):
            for k, v in front_part.items():
                # append back items
                joined_parms[k] = v
        elif isinstance(front_part, list):
            for item in front_part:
                # split item  on '=' eg. patient=4995802
                item_split = item.split('=')
                if len(item_split) > 1:
                    joined_parms[item_split[0]] = item_split[1]
                else:
                    joined_parms[item_split[0]] = ''

    if len(back_part) > 0:
        if isinstance(back_part, dict):
            for k, v in back_part.items():
                # append back items
                joined_parms[k] = v
        elif isinstance(back_part, list):
            for item in back_part:
                # split item  on '=' eg. patient=4995802
                item_split = item.split('=')
                if len(item_split) > 1:
                    joined_parms[item_split[0]] = item_split[1]
                else:
                    joined_parms[item_split[0]] = ''

    concat_parms = '?' + urlencode(joined_parms)

    # logger.debug('resulting string:%s' % concat_parms)

    # We have to do something
    # joined_parms = '?'
    #
    # if len(front_part) != 0:
    #     joined_parms += front_part
    #
    # if len(back_part) == 0:
    #     # nothing to add
    #     return joined_parms
    # else:
    #     joined_parms += '&' + back_part

    return concat_parms


def build_params(get, srtc, key):
    """
    Build the URL Parameters.
    We have to skip any in the skip list.

    :param get:
    :return:
    """
    # We will default to json for content handling
    # FIXME: variables not used
    # in_fmt = 'json'
    # pass_to = ''

    # First we strip the parameters that need to be blocked
    url_param = block_params(get, srtc)

    # Now we need to construct the parameters we need to add
    add_param = add_params(srtc, key)

    # Put the parameters together in urlencoded string
    # leading ? and parameters joined by &
    all_param = concat_parms(url_param, add_param)

    # logger.debug('Parameter (post block/add):%s' % all_param)

    # now we check for _format being specified. Otherwise we get back html
    # by default we will process json unless _format is already set.

    all_param = add_format(all_param)

    # logger.debug('add_Format returned:%s' % all_param)

    return all_param


def add_format(all_param=''):
    """ Check for _format in parameters and add if missing """

    if '_format' in all_param:
        # We have a _format setting.
        # Let's check for xml or json.
        if '_format=json' in all_param.lower():
            return all_param
        elif '_format=xml' in all_param.lower():
            return all_param

    # no _format set.
    # Let's set _format=json.
    if all_param != '':
        all_param += '&'
    else:
        all_param = '?'

    all_param += '_format=json'

    return all_param


def get_url_query_string(get, skip_parm=[]):
    """
    Receive the request.GET Query Dict
    Evaluate against skip_parm by skipping any entries in skip_parm
    Return a query string ready to pass to a REST API.
    http://hl7-fhir.github.io/search.html#all

    # We need to force the key to lower case and skip params should be
    # lower case too

    eg. _lastUpdated=>2010-10-01&_tag=http://acme.org/codes|needs-review

    :param get: {}
    :param skip_parm: []
    :return: Query_String (QS)
    """
    # logger.debug('Evaluating: %s to remove:%s' % (get,skip_parm))

    filtered_dict = OrderedDict()

    # Check we got a get dict
    if not get:
        return filtered_dict
    if not isinstance(get, dict):
        return filtered_dict

    # Now we work through the parameters

    for k, v in get.items():

        # logger.debug('K/V: [%s/%s]' % (k,v))

        if k in skip_parm:
            pass
        else:
            # Build the query_string
            filtered_dict[k] = v

    # qs = urlencode(filtered_dict)
    qs = filtered_dict

    # logger.debug('Filtered parameters:%s from:%s' % (qs, filtered_dict))
    return qs


def FhirServerUrl(server=None, path=None, release=None):
    # fhir_server_configuration =
    # {'SERVER':'http://fhir-test.bbonfhir.com:8081',
    #                              'PATH':'/',
    #                              'RELEASE':'/baseDstu2'}
    # FHIR_SERVER_CONF = fhir_server_configuration
    # FHIR_SERVER = FHIR_SERVER_CONF['SERVER'] + FHIR_SERVER_CONF['PATH']

    # print("server[%s] or %s" % (server,settings.FHIR_SERVER_CONF['SERVER']))
    # print("path[%s]" % path)
    # print("release[%s]" % release)

    fhir_server = notNone(server, settings.FHIR_SERVER_CONF['SERVER'])

    fhir_path = notNone(path, settings.FHIR_SERVER_CONF['PATH'])

    fhir_release = notNone(release, settings.FHIR_SERVER_CONF['RELEASE'])

    if fhir_release is not None:
        if not fhir_release.endswith('/'):
            fhir_release += '/'

    result = fhir_server
    if result is not None:
        result += fhir_path
    if result is not None:
        result += fhir_release
    # Set to "" if still None
    if result is None:
        result = ""

    return result


def check_access_interaction_and_resource_type(resource_type, intn_type):
    try:
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        # force comparison to lower case to make case insensitive check
        if intn_type.lower() not in map(str.lower,
                                        rt.get_supported_interaction_types()):
            msg = 'The interaction: %s is not permitted on %s FHIR ' \
                  'resources on this FHIR sever.' % (intn_type,
                                                     resource_type)
            return kickout_403(msg)
    except SupportedResourceType.DoesNotExist:
        msg = '%s is not a supported resource ' \
              'type on this FHIR server.' % resource_type
        return kickout_404(msg)

    return False


def check_rt_controls(resource_type):
    # Check for controls to apply to this resource_type
    # logger.debug('Resource_Type =%s' % resource_type)
    try:
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
    except SupportedResourceType.DoesNotExist:
        srtc = None
        return srtc

    # logger.debug('Working with SupportedResourceType:%s' % rt)

    try:
        srtc = ResourceTypeControl.objects.get(resource_name=rt)
    except ResourceTypeControl.DoesNotExist:
        srtc = None
        # srtc = {}
        # srtc['empty'] = True
        # srtc['resource_name'] = ''
        # srtc['override_url_id'] = False
        # srtc['override_search'] = False
        # srtc['search_block'] = ['',]
        # srtc['search_add'] = ['',]
        # srtc['group_allow'] = ''
        # srtc['group_exclude'] = ''
        # srtc['default_url'] = ''

    return srtc


def masked(srtc=None):
    """ check if force_url_override is set in SupportedResourceType """
    mask = False
    if srtc:
        if srtc.override_url_id:
            mask = True

    return mask


def masked_id(res_type,
              crosswalk=None,
              srtc=None,
              orig_id=None,
              slash=True):
    """ Get the correct id
     if crosswalk.fhir_source.shard_by == resource_type

     """
    id = str(orig_id)
    if srtc:
        if srtc.override_url_id:
            if crosswalk:
                if res_type.lower() == crosswalk.fhir_source.shard_by.lower():
                    # logger.debug('Replacing %s
                    # with %s' % (id, crosswalk.fhir_id))
                    id = crosswalk.fhir_id

    if slash:
        id += '/'

    return id


def mask_with_this_url(request, host_path='', in_text='', find_url=''):
    """ find_url in in_text and replace with url for this server """

    if in_text == '':
        # No text to evaluate
        return in_text

    if find_url == '':
        # no string to find
        return in_text

    # Now we have something to do
    # Get the host name
    # replace_text = request.get_host()
    if host_path.endswith('/'):
        host_path = host_path[:-1]

    out_text = in_text.replace(find_url, host_path)

    # logger.debug('Replacing: [%s] with [%s]' % (find_url, host_path))

    return out_text


def mask_list_with_host(request, host_path, in_text, urls_be_gone=[]):
    """ Replace a series of URLs with the host_name """

    if in_text == '':
        # No text to evaluate
        return in_text

    if len(urls_be_gone) == 0:
        # Nothing in the list to be replaced
        return in_text

    if isinstance(settings.FHIR_SERVER_CONF['REWRITE_FROM'], list):
        for u in settings.FHIR_SERVER_CONF['REWRITE_FROM']:
            if u not in urls_be_gone:
                urls_be_gone.append(u)
    elif isinstance(settings.FHIR_SERVER_CONF['REWRITE_FROM'], str):
        if not settings.FHIR_SERVER_CONF['REWRITE_FROM'] in urls_be_gone:
            urls_be_gone.append(settings.FHIR_SERVER_CONF['REWRITE_FROM'])

    for kill_url in urls_be_gone:
        # work through the list making replacements
        if kill_url.endswith('/'):
            kill_url = kill_url[:-1]

        # print("Replacing:%s" % kill_url)

        in_text = mask_with_this_url(request, host_path, in_text, kill_url)

    return in_text


def get_host_url(request, resource_type=''):
    """ get the full url and split on resource_type """

    if request.is_secure():
        http_mode = 'https://'
    else:
        http_mode = 'http://'

    full_url = http_mode + request.get_host() + request.get_full_path()
    if resource_type == '':
        return full_url
    else:
        full_url_list = full_url.split(resource_type)

    # logger.debug('Full_url as list:%s' % full_url_list)

    return full_url_list[0]

def pretty_json(od, indent=PRETTY_JSON_INDENT):
    """ Print OrderedDict as pretty indented JSON """

    return json.dumps(od, indent=indent)
