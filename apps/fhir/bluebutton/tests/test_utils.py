import os
import uuid
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from apps.accounts.models import UserProfile
from apps.test import BaseApiTest
from apps.fhir.bluebutton.models import Crosswalk

from apps.fhir.bluebutton.utils import (
    notNone,
    FhirServerAuth,
    mask_with_this_url,
    get_host_url,
    prepend_q,
    dt_patient_reference,
    crosswalk_patient_id,
    get_resourcerouter,
    build_oauth_resource,
)

ENCODED = settings.ENCODING


class BluebuttonUtilsSimpleTestCase(BaseApiTest):
    # Load fixtures
    fixtures = ['fhir_bluebutton_test_rt.json',
                'fhir_bluebutton_new_testdata.json']

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


class BlueButtonUtilSupportedResourceTypeControlTestCase(TestCase):

    fixtures = ['fhir_bluebutton_new_testdata.json']

    def test_FhirServerAuth(self):
        """  Check FHIR Server ClientAuth settings """

        """ Test 1: pass nothing"""

        resource_router = get_resourcerouter()
        expected = {}
        expected['client_auth'] = resource_router.client_auth
        expected['cert_file'] = os.path.join(settings.FHIR_CLIENT_CERTSTORE,
                                             resource_router.cert_file)
        expected['key_file'] = os.path.join(settings.FHIR_CLIENT_CERTSTORE,
                                            resource_router.key_file)

        response = FhirServerAuth()

        self.assertDictEqual(response, expected)

    def test_prepend_q_yes(self):
        """ Check that ? is added to front of parameters if required """

        pass_params = "test=one&test=2&test=3"
        response = prepend_q(pass_params)

        expected = "?" + pass_params

        self.assertEquals(response, expected)

    def test_prepend_q_no(self):
        """ Check that ? is not added to front of parameters if required """

        pass_params = "?test=one&test=2&test=3"
        response = prepend_q(pass_params)

        expected = pass_params

        self.assertEquals(response, expected)


class BlueButtonUtilRequestTest(TestCase):

    fixtures = ['fhir_bluebutton_test_rt.json']

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


class Patient_Resource_Test(BaseApiTest):

    """ Testing for Patient/id DT resource from Crosswalk """

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='fred4', email='fred4@...', password='top_secret')

        xwalk = Crosswalk()
        xwalk.user = self.user
        xwalk.fhir_id = "Patient/12345"
        xwalk.user_hicn_hash = uuid.uuid4()
        xwalk.user_mbi_hash = uuid.uuid4()
        xwalk.save()

    def test_crosswalk_fhir_id(self):
        """ Get the Crosswalk FHIR_Id """

        u = User.objects.create_user(username="billybob",
                                     first_name="Billybob",
                                     last_name="Button",
                                     email='billybob@example.com',
                                     password="foobar", )
        UserProfile.objects.create(user=u,
                                   user_type="DEV",
                                   create_applications=True)

        x = Crosswalk()
        x.user = u
        x.fhir_id = "Patient/23456"
        x.user_hicn_hash = uuid.uuid4()
        x.user_mbi_hash = uuid.uuid4()
        x.save()

        result = crosswalk_patient_id(u)

        self.assertEqual(x.fhir_id, result)

        # Test the dt_reference for Patient

        result = dt_patient_reference(u)

        expect = {'reference': x.fhir_id}

        self.assertEqual(result, expect)

    def test_crosswalk_not_fhir_id(self):
        """ Get no Crosswalk id """

        u = User.objects.create_user(username="bobnobob",
                                     first_name="bob",
                                     last_name="Button",
                                     email='billybob@example.com',
                                     password="foobar", )

        result = crosswalk_patient_id(u)

        self.assertEqual(result, None)

        # Test the dt_reference for Patient returning None

        result = dt_patient_reference(u)

        self.assertEqual(result, None)


class Security_Metadata_test(BaseApiTest):
    """
    Testing for security content addition
    """

    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()

    def test_oauth_resource_empty(self):
        """
        Test build_oauth_resource with no parameters
        """
        request = self.factory.get('/cmsblue/fhir/v1/metadata')

        result = build_oauth_resource(request)

        expected = True

        self.assertEqual(result['cors'], expected)

    def test_oauth_resource_json(self):
        """
        Test build_oauth_resource with json
        """
        request = self.factory.get('/cmsblue/fhir/v1/metadata')

        result = build_oauth_resource(request, "json")

        expected = True

        self.assertEqual(result['cors'], expected)

    def test_oauth_resource_xml(self):
        """
        Test build_oauth_resource with xml
        """
        request = self.factory.get('/cmsblue/fhir/v1/metadata')

        result = build_oauth_resource(request, "xml")

        expected = "<cors>true</cors>"

        # print(result[16:33])

        self.assertEqual(result[16:33], expected)
