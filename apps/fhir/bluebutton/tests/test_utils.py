import urllib

from collections import OrderedDict

from django.conf import settings
from django.test import TestCase, RequestFactory

from apps.test import BaseApiTest

from apps.fhir.bluebutton.models import (ResourceTypeControl,
                                         SupportedResourceType,
                                         Crosswalk)

from apps.fhir.bluebutton.utils import (
    notNone,
    strip_oauth,
    block_params,
    add_params,
    concat_parms,
    build_params,
    add_format,
    get_url_query_string,
    FhirServerUrl,
    check_access_interaction_and_resource_type,
    check_rt_controls,
    masked,
    masked_id,
    mask_with_this_url,
    mask_list_with_host,
    get_host_url,
    pretty_json
)


ENCODED = settings.ENCODING


class BluebuttonUtilsSimpleTestCase(BaseApiTest):
    # Create a user
    # username = "bobby"
    # password = "password"
    # user = User.objects._create_user(username,
    #                                  password=password,
    #                                  email="bob@example.net")
    # created a default user
    # logger.debug("user: '%s[%s]'" % (user,user.pk))

    # Now load fixtures
    fixtures = ['fhir_bluebutton_testdata.json']

    def test_notNone(self):
        """ Test notNone return values """

        response = notNone("MATCH", "MATCH")
        self.assertEqual(response, "MATCH")

        # Empty is not NONE
        response = notNone("", "MATCH")
        self.assertNotEqual(response, "MATCH")

        # None returns "Default"
        response = notNone(None, "Default")
        self.assertEqual(response, "Default")

        # No values
        response = notNone()
        self.assertEqual(response, None)

        # No Default supplied - None Returns None
        response = notNone(None)
        self.assertEqual(response, None)

        # No Default supplied - Match Returns Match
        response = notNone("Match")
        self.assertEqual(response, "Match")

        # 1 returns 1
        value = 1
        response = notNone(value, "number")
        self.assertEqual(response, 1)

        # undefined returns default
        undefinedvalue = None
        response = notNone(undefinedvalue, "default")
        self.assertEqual(response, "default")

        # List returns list
        listing = [1, 2, 3]
        response = notNone(listing, "number")
        self.assertEqual(response, listing)

    def test_strip_oauth(self):
        """ test request.GET removes OAuth parameters """

        # <QueryDict: {'_format': ['json']}>
        get_ish_1 = {
            '_format': ['json'],
            'access_token': ['some_Token'],
            'state': ['some_State'],
            'response_type': ['some_Response_Type'],
            'client_id': ['Some_Client_id'],
            'Keep': ['keep_this'],
        }

        get_ish_2 = {
            '_format': ['json'],
            'Keep': ['keep_this'],
        }

        get_ish_3 = {
            'access_token': ['some_Token'],
            'state': ['some_State'],
            'response_type': ['some_Response_Type'],
            'client_id': ['Some_Client_id'],
        }

        get_ish_4 = {}

        response = strip_oauth(get_ish_1)
        self.assertEqual(response, get_ish_2, "Successful removal")

        response = strip_oauth(get_ish_3)
        self.assertEqual(response, get_ish_4, "Successful removal of all items")

        response = strip_oauth(get_ish_2)
        self.assertEqual(response, get_ish_2, "Nothing removed")

        response = strip_oauth(get_ish_4)
        self.assertEqual(response, get_ish_4, "Empty dict - nothing to do")

        response = strip_oauth()
        self.assertEqual(response, {}, "Empty dict - nothing to do")

    def test_block_params(self):
        """
        strip parameters from get dict based on list in ResoureTypeControl record
        """

        srtc = ResourceTypeControl.objects.get(pk=2)

        # <QueryDict: {'_format': ['json']}>
        get_ish_1 = {
            '_format': ['json'],
            'access_token': ['some_Token'],
            'state': ['some_State'],
            'response_type': ['some_Response_Type'],
            'client_id': ['Some_Client_id'],
            'keep': ['keep_this'],
        }

        get_ish_2 = {
            'access_token': ['some_Token'],
            'state': ['some_State'],
            'client_id': ['Some_Client_id'],
            'keep': ['keep_this'],
        }

        # TODO: this is not used
        # get_ish_3 = {
        #     '_format': ['json'],
        #     'access_token': ['some_Token'],
        #     'state': ['some_State'],
        #     'claim': ['some_Claim'],
        #     'claimresponse': ['some_ClaimResponse'],
        #     'response_type': ['some_Response_Type'],
        #     'client_id': ['Some_Client_id'],
        #     'keep': ['keep_this'],
        # }

        get_ish_4 = {
            'access_token': ['some_Token'],
            'state': ['some_State'],
            'claimresponse': ['some_ClaimResponse'],
            'response_type': ['some_Response_Type'],
            'client_id': ['Some_Client_id'],
            'keep': ['keep_this'],
        }

        response = block_params(get_ish_1, srtc)
        for k, v in response.items():
            if k in get_ish_2:
                self.assertEquals(v, get_ish_2[k])

        srtc = ResourceTypeControl.objects.get(pk=3)
        response = block_params(get_ish_4, srtc)
        for k, v in response.items():
            if k in get_ish_4:
                self.assertEquals(v, get_ish_4[k])

    def test_pretty_json(self):
        """ Test text dict or list is converted to pretty json(indent=4) """

        od = '{"format": ["application/xml+fhir","application/json+fhir"]}'
        response = pretty_json(od, indent=5)
        expected = '"{\\"format\\": [\\"application/xml+fhir\\",\\"application/json+fhir\\"]}"'

        self.assertEqual(response, expected)


class BlueButtonUtilSrtcTestCase(TestCase):

    fixtures = ['fhir_bluebutton_testdata.json']

    def test_add_params(self):
        """
        Add parameters to search parameters by returning a list

            - srtc exists override_search is True and data in search_add
            - srtc.exists and search_add is empty
            - srtc.exists but override_search is false
            - srtc is None
        """
        # Create a user
        # username = "john"
        # password = "password"
        # user = User.objects.create_user(username, password=password )
        # # created a default user

        # Test
        srtc = ResourceTypeControl.objects.get(pk=1)
        Crosswalk.objects.get(pk=1)
        fhir_id = "4995802"
        response = add_params(srtc, fhir_id)
        self.assertEquals(response, ['patient=4995802'])

        # Test
        srtc = ResourceTypeControl.objects.get(pk=2)
        Crosswalk.objects.get(pk=1)
        fhir_id = "4995802"
        response = add_params(srtc, fhir_id)
        self.assertEquals(response, [])

        # Test
        srtc = ResourceTypeControl.objects.get(pk=1)
        Crosswalk.objects.get(pk=1)
        response = add_params(srtc)
        self.assertEquals(response, ['patient='])

        # Test
        srtc = ResourceTypeControl.objects.get(pk=3)
        Crosswalk.objects.get(pk=1)
        response = add_params(srtc)
        self.assertEquals(response, [])

        # Test
        srtc = None
        Crosswalk.objects.get(pk=1)
        response = add_params(srtc)
        self.assertEquals(response, [])

    def test_concat_params(self):
        """
        Test the concatenation of parameters; test receiving a list instead of
        a dict or OrderedDict

            - Test front = OrderedDict / back = OrderedDict
            - Test front = OrderedDict / back = None
            - Test front = OrderedDict / back = List
            - Test front = OrderedDict / back = Partial List ['patient=']
            - Test front = List / back = List
        """

        # Test 1
        front = OrderedDict([('a', 2), ('b', "Bee"), ('c', True)])
        back = OrderedDict([('d', 4), ('e', "Eric"), ('f', False)])
        result = "?a=2&b=Bee&c=True&d=4&e=Eric&f=False"
        response = concat_parms(front, back)
        self.assertEquals(response, result)

        # Test 2
        front = OrderedDict([('a', 2), ('b', 'Bee'), ('c', True)])

        result = '?a=2&b=Bee&c=True'

        response = concat_parms(front)
        self.assertEquals(response, result)

        # Test 3
        front = OrderedDict([('a', 2), ('b', 'Bee'), ('c', True)])
        back = ['d=4', 'e=Eric', 'f=False']
        result = '?a=2&b=Bee&c=True&d=4&e=Eric&f=False'
        response = concat_parms(front, back)
        self.assertEquals(response, result)

        # Test 4
        front = OrderedDict([('a', 2), ('b', 'Bee'), ('c', True)])
        back = ['d=4', 'e=', 'f=False']
        result = '?a=2&b=Bee&c=True&d=4&e=&f=False'
        response = concat_parms(front, back)
        self.assertEquals(response, result)

        # Test 5
        front = ['a=2', 'b=Bee', 'c=True']
        back = ['d=4', 'e=', 'f=False']
        result = "?a=2&b=Bee&c=True&d=4&e=&f=False"
        response = concat_parms(front, back)
        self.assertEquals(response, result)

    def test_build_params(self):
        """
        Test Build Params
        This involves skipping items in the ResourceTypeControl.search_block
        using block_params and then adding additions us add_params
        Then concatenating the two using concat_params.

            - Test 1: Get has parameters. SRTC is valid and Key (FHIR_ID) is good
            - Test 2: Get - No parameters, SRTC Valid, Key is good
            - Test 3: GET has parameters, SRTC is None, key is empty
        """

        # Test 1: Get has parameters. SRTC is valid and Key (FHIR_ID) is good
        # <QueryDict: {'_format': ['json']}>
        get_ish_1 = {
            '_format': 'json',
            'keep': 'keep_this',
            'claim': '123456',
            'resource_type': 'some_resource',
        }
        srtc = ResourceTypeControl.objects.get(pk=4)
        fhir_id = '4995802'
        response = build_params(get_ish_1, srtc, fhir_id)
        expected = '?keep=keep_this&patient=4995802&_format=json'
        self.assertEquals(response, expected)

        # Test 2: Get - No parameters, SRTC Valid, Key is good
        get_ish_2 = {}
        response = build_params(get_ish_2, srtc, fhir_id)
        expected = '?patient=4995802&_format=json'
        self.assertEquals(response, expected)

        # Test 3: GET has parameters, SRTC is None, key is empty
        srtc = None
        key = ''
        response = build_params(get_ish_1, srtc, key)
        resp_dict = dict(urllib.parse.parse_qsl(response[1:]))
        expected = '?keep=keep_this&resource_type=some_resource&_format=json&claim=123456'
        expe_dict = dict(urllib.parse.parse_qsl(expected[1:]))
        self.assertDictEqual(resp_dict, expe_dict)

    def test_add_format(self):
        """ Check for _format and add """

        # Test 1: Empty encoded string, add _format=json
        param_string = ''
        response = add_format(param_string)
        expected = '?_format=json'
        self.assertEquals(response, expected)

        # Test 2: _format=xml, return unchanged
        param_string = 'keep=anything&_format=xml'
        response = add_format(param_string)
        expected = 'keep=anything&_format=xml'
        self.assertEquals(response, expected)

        # Test 3: _format=json, return unchanged
        param_string = 'keep=anything&_format=json'
        response = add_format(param_string)
        expected = 'keep=anything&_format=json'
        self.assertEquals(response, expected)

        # Test 4: _format=JSon, return unchanged
        param_string = 'keep=anything&_format=JSon'
        response = add_format(param_string)
        expected = 'keep=anything&_format=JSon'
        self.assertEquals(response, expected)

    def test_get_url_query_string(self):
        """ Test get_url_query_String """

        """ Test 1: """
        get_ish_1 = {
            '_format': ['json'],  # TODO: will be removed
            'access_token': ['some_Token'],
            'state': ['some_State'],
            'resource_type': ['some_Resourse_Type'],  # TODO: will be removed
            'client_id': ['Some_Client_id'],
            'keep': ['keep_this'],
        }

        srtc = ResourceTypeControl.objects.get(pk=2)

        response = get_url_query_string(get_ish_1, srtc.search_block)

        response_sorted = OrderedDict()
        for key, value in sorted(response.items()):
            response_sorted[key] = value

        # "[\"patient\",\"_format\",\"resource_type\"]"
        expected = OrderedDict()
        expected['access_token'] = ['some_Token']
        expected['client_id'] = ['Some_Client_id']
        expected['keep'] = ['keep_this']
        expected['state'] = ['some_State']
        self.assertEquals(response_sorted, expected)

        """ Test 2 empty call """
        response = get_url_query_string({})
        expected = OrderedDict()
        self.assertEquals(response, expected)

        """ Test 3 call with empty list """
        response = get_url_query_string([])
        expected = OrderedDict()
        self.assertEquals(response, expected)

        """ Test 4 call with list """
        response = get_url_query_string(['a=a', 'b=b', 'c=3'])
        expected = OrderedDict()
        self.assertEquals(response, expected)

    def test_FhirServerUrl(self):
        """ Build a fhir server url """

        """ Test 1: Pass all parameters """
        response = FhirServerUrl('http://localhost:8000', '/any_path', '/release')
        expected = 'http://localhost:8000/any_path/release/'
        self.assertEquals(response, expected)

        """ Test 2: Pass no parameters """
        response = FhirServerUrl()

        # Should pull from _start.settings.base.py
        # FHIR_SERVER_CONF = {"SERVER":"http://fhir.bbonfhir.com/",
        #            "PATH":"fhir-p/",
        #            "RELEASE":"baseDstu2/",
        #            "REWRITE_FROM":"http://ec2-52-4-198-86.compute-1.
        #                            amazonaws.com:8080/baseDstu2",
        #            "REWRITE_TO":"http://localhost:8000/bluebutton/fhir/v1"}

        expected = 'http://fhir.bbonfhir.com/fhir-p/baseDstu2/'
        self.assertEquals(response, expected)

    def test_check_access_interaction_and_resource_type(self):
        """ test resource_type and interaction_type from SupportedResourceType """

        """ Test 1: Patient GET = True """
        resource_type = 'Patient'
        interaction_type = 'get'  # True
        response = check_access_interaction_and_resource_type(resource_type, interaction_type)
        self.assertEquals(response, False)

        """ Test 2: Patient get = True """
        resource_type = 'Patient'
        interaction_type = 'GET'  # True
        response = check_access_interaction_and_resource_type(resource_type, interaction_type)
        self.assertEquals(response, False)

        """ Test 3: Patient UPdate = False """
        resource_type = 'Patient'
        interaction_type = 'UPdate'  # False
        response = check_access_interaction_and_resource_type(resource_type, interaction_type)
        self.assertEquals(response.status_code, 403)

        """ Test 4: Patient UPdate = False """
        resource_type = 'BadResourceName'
        interaction_type = 'get'  # False
        response = check_access_interaction_and_resource_type(resource_type, interaction_type)
        self.assertEquals(response.status_code, 404)


class BlueButtonUtilsRtTestCase(TestCase):

    fixtures = ['fhir_bluebutton_test_rt.json']

    def test_check_rt_controls(self):
        """ Get ResourceTypeControl via SupportedResourceType from resource_type """

        """ Test 1: Good Resource """
        resource_type = 'Patient'

        response = check_rt_controls(resource_type)
        expect = SupportedResourceType.objects.get(resource_name=resource_type)
        # print("Resource:", response.resource_name.id,"=", expected.id)

        self.assertEquals(response.resource_name.id, expect.id)

        """ Test 2: Bad Resource """
        resource_type = 'BadResource'

        response = check_rt_controls(resource_type)

        self.assertEquals(response, None)

    def test_masked(self):
        """ Checking for srtc.override_url_id """

        """ Test:1 srtc with valid override_url_id=True """

        srtc = ResourceTypeControl.objects.get(pk=1)

        response = masked(srtc)
        expected = True

        self.assertEqual(response, expected)

        """ Test:2 srtc with valid override_url_id=False """

        srtc = ResourceTypeControl.objects.get(pk=4)

        response = masked(srtc)
        expected = False

        self.assertEqual(response, expected)

        """ Test:3 srtc =None """

        srtc = ResourceTypeControl.objects.get(pk=1)

        response = masked(None)
        expected = False

        self.assertEqual(response, expected)

        """ Test:4 No SRTC """

        # srtc = ResourceTypeControl.objects.get(pk=1)

        response = masked()
        expected = False

        self.assertEqual(response, expected)

    def test_masked_id(self):
        """ Get the correct id using masking """

        """ Test 1: Patient replace 1 with 49995802/ """

        resource_type = 'Patient'
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        r_id = 1

        srtc = ResourceTypeControl.objects.get(resource_name=rt.id)
        cx = Crosswalk.objects.get(user=1)

        response = masked_id(resource_type, cx, srtc, r_id)
        expected = '4995802/'

        self.assertEqual(response, expected)

        """ Test 2: Patient replace 1 with 49995802 """

        resource_type = 'Patient'
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        r_id = 1

        srtc = ResourceTypeControl.objects.get(resource_name=rt.id)
        cx = Crosswalk.objects.get(user=1)

        response = masked_id(resource_type, cx, srtc, r_id, False)
        expected = '4995802'

        self.assertEqual(response, expected)

        """ Test 3: ClaimResponse Don't replace id just add slash """

        resource_type = 'ClaimResponse'
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        r_id = 1

        srtc = ResourceTypeControl.objects.get(resource_name=rt.id)
        cx = Crosswalk.objects.get(user=1)

        response = masked_id(resource_type, cx, srtc, r_id)
        expected = '1/'

        self.assertEqual(response, expected)

        """ Test 4: ClaimResponse Don't replace id """

        resource_type = 'ClaimResponse'
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        r_id = 1

        srtc = ResourceTypeControl.objects.get(resource_name=rt.id)
        cx = Crosswalk.objects.get(user=1)

        response = masked_id(resource_type, cx, srtc, r_id, False)
        expected = '1'

        self.assertEqual(response, expected)

        """ Test 5: No Crosswalk """

        resource_type = 'ClaimResponse'
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        r_id = 1

        srtc = ResourceTypeControl.objects.get(resource_name=rt.id)
        cx = Crosswalk.objects.get(user=1)

        response = masked_id(resource_type, None, srtc, r_id)
        expected = '1/'

        self.assertEqual(response, expected)

        """ Test 6: No SRTC """

        resource_type = 'ClaimResponse'
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        r_id = 1

        srtc = ResourceTypeControl.objects.get(resource_name=rt.id)
        cx = Crosswalk.objects.get(user=1)

        response = masked_id(resource_type, cx, None, r_id)
        expected = '1/'

        self.assertEqual(response, expected)


class BlueButtonUtilRequestTest(TestCase):

    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()

    def test_mask_with_this_url(self):
        """ Replace one url with another in a text string """

        """ Test 1: No text to replace. No changes """

        input_text = 'dddd anything http://www.example.com:8000 ' \
                     'will get replaced'
        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        response = mask_with_this_url(request,
                                      host_path='http://www.replaced.com',
                                      in_text='',
                                      find_url='http://www.example.com:8000')

        expected = ''

        self.assertEqual(response, expected)

        """ Test 2: No text to replace with. No changes """

        input_text = 'dddd anything http://www.example.com:8000 ' \
                     'will get replaced'
        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        response = mask_with_this_url(request,
                                      host_path='http://www.replaced.com',
                                      in_text=input_text,
                                      find_url='')

        expected = input_text

        self.assertEqual(response, expected)

        """ Test 3: Replace text removing slash from end of replaced text """

        input_text = 'dddd anything http://www.example.com:8000 ' \
                     'will get replaced'
        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        response = mask_with_this_url(request,
                                      host_path='http://www.replaced.com/',
                                      in_text=input_text,
                                      find_url='http://www.example.com:8000')

        expected = 'dddd anything http://www.replaced.com will get replaced'

        self.assertEqual(response, expected)

        """ Test 4: Replace text """

        input_text = 'dddd anything http://www.example.com:8000 ' \
                     'will get replaced'
        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        response = mask_with_this_url(request,
                                      host_path='http://www.replaced.com',
                                      in_text=input_text,
                                      find_url='http://www.example.com:8000')

        expected = 'dddd anything http://www.replaced.com will get replaced'

        self.assertEqual(response, expected)

    def test_mask_list_with_host(self):
        """ Replace urls in list with host_path in a text string """

        # FHIR_SERVER_CONF = {
        #   "SERVER": "http://fhir.bbonfhir.com/",
        #   "PATH": "fhir-p/",
        #   "RELEASE": "baseDstu2/",
        #   "REWRITE_FROM": "http://ec2-52-4-198-86.compute-1.amazonaws.com" \
        #                   ":8080/baseDstu2",
        #   "REWRITE_TO": "http://localhost:8000/bluebutton/fhir/v1"}

        """ Test 1: No text to replace. No changes """

        request = self.factory.get('/cmsblue/fhir/v1/Patient')

        input_text = 'dddd anything http://ec2-52-4-198-86.compute-1.' \
                     'amazonaws.com:8080/baseDstu2 will get replaced ' \
                     'more stuff http://www.example.com:8000 and ' \
                     'http://example.com:8000/ okay'

        response = mask_list_with_host(request,
                                       'http://www.replaced.com',
                                       '',
                                       ['http://www.example.com:8000',
                                        'http://example.com'])

        expected = ''
        self.assertEqual(response, expected)

        """ Test 2: No text to replace with. Only replace
            FHIR_SERVER_CONF.REWRITE_FROM changes
        """

        input_text = 'dddd anything http://ec2-52-4-198-86.compute-1.' \
                     'amazonaws.com:8080/baseDstu2 will get replaced ' \
                     'more stuff http://www.example.com:8000 and ' \
                     'http://example.com:8000/ okay'

        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        response = mask_list_with_host(request,
                                       'http://www.replaced.com',
                                       input_text,
                                       [])

        expected = input_text

        self.assertEqual(response, expected)

        """ Test 3: Replace text removing slash from end of replaced text """

        input_text = 'dddd anything http://ec2-52-4-198-86.compute-1.' \
                     'amazonaws.com:8080/baseDstu2 will get replaced ' \
                     'more stuff http://www.example.com:8000 and ' \
                     'http://example.com:8000/ okay'

        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        response = mask_list_with_host(request,
                                       'http://www.replaced.com/',
                                       input_text,
                                       ['http://www.example.com:8000',
                                        'http://example.com'])

        expected = 'dddd anything http://www.replaced.com will get replaced ' \
                   'more stuff http://www.replaced.com and ' \
                   'http://www.replaced.com:8000/ okay'

        self.assertEqual(response, expected)

        """ Test 4: Replace text """

        input_text = 'dddd anything http://ec2-52-4-198-86.compute-1.' \
                     'amazonaws.com:8080/baseDstu2 will get replaced ' \
                     'more stuff http://www.example.com:8000 and ' \
                     'http://example.com:8000/ okay'

        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        response = mask_list_with_host(request,
                                       'http://www.replaced.com',
                                       input_text,
                                       ['http://www.example.com:8000',
                                        'http://example.com'])

        expected = 'dddd anything http://www.replaced.com will get replaced ' \
                   'more stuff http://www.replaced.com and ' \
                   'http://www.replaced.com:8000/ okay'

        self.assertEqual(response, expected)

    def test_get_host_ur_good(self):
        """
        Get the host url and split on resource_type
        """

        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        response = get_host_url(request, 'Patient')
        expected = 'http://testserver/cmsblue/fhir/v1/'

        self.assertEqual(response, expected)

    def test_get_host_ur_no_rt(self):
        """
        Get the host url and split on empty resource_type
        """
        request = self.factory.get('/cmsblue/fhir/v1/Patient')

        response = get_host_url(request)
        expected = 'http://testserver/cmsblue/fhir/v1/Patient'

        self.assertEqual(response, expected)
