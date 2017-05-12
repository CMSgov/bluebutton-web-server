import json
from random import randrange

# from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, RequestFactory
try:
    # python 3 - Mock is now a standard module in unittest
    from unittest.mock import patch
except ImportError:
    # python 2 - Mock needs to be pip installed
    from mock import patch   # NOQA

# import apps.fhir.testac.views

import os

from django.conf import settings
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import pretty_json
from apps.fhir.testac.views.base import bb_upload, check_crosswalk
from .test_harness import FakeMessages, MessagingRequest
# Create your tests here.

from ..utils.sample_data_bb import SAMPLE_BB_TEXT
from ..utils.sample_json_bb import SAMPLE_BB_JSON
# from ..utils.sample_json_bb_claim import SAMPLE_BB_CLAIM_PART_A
from ..views.base import bb_to_eob


class BaseDIRTest(TestCase):
    """ Check the settings.BASEDIR """

    def test_basedir(self):
        """
        Check the BASEDIR in settings
        """
        base = settings.BASE_DIR
        expect = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        expected = os.path.join(base, '..')
        if expect == expected:
            pass
        # print("\nBASE_DIR:%s" % base)
        # print("\nabspath:%s" % expect)
        # print("\nparent:%s" % expected)

        self.assertEqual(base.endswith(".."), True)


class PostBlueButtonFileTest(TestCase):
    """ Test the BlueButton Upload """

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='jacob', email='jacob@...', password='top_secret')

    def test_not_logged_in_fail(self):
        """ BBUpload - User not logged in """

        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = AnonymousUser()

        format = "html"
        payload = {"bb_text": SAMPLE_BB_TEXT,
                   "output_format": format}
        result = bb_upload(request, payload)

        # print("Result:%s" % result)

        self.assertEqual(result.status_code,
                         302)

    def test_user_logged_in_success_html(self):
        """ BBUpload - User Logged in """

        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = self.user

        format = "html"
        payload = {"bb_text": SAMPLE_BB_TEXT,
                   "output_format": format}
        result = bb_upload(request, payload)

        # print("Result:%s" % result)

        self.assertEqual(result.status_code,
                         200)

    def test_user_logged_in_success_json(self):
        """ BBUpload - User Logged in """

        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = self.user

        format = "json"
        payload = {"bb_text": SAMPLE_BB_TEXT,
                   "output_format": format}
        result = bb_upload(request, payload)

        # print("Result:%s" % result)

        self.assertEqual(result.status_code,
                         200)


class CheckCrossWalkForRequestUserTest(TestCase):
    """ Check Crosswalk before giving access to bbupload """

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.factory = RequestFactory()
        self.messages = MessagingRequest()
        self.user = User.objects.create_user(
            username='jacob', email='jacob@...', password='top_secret')

    def test_not_logged_in_fail(self):
        """ check_crosswalk - User not logged in """

        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = AnonymousUser()

        result = check_crosswalk(request)

        # print("Result:%s" % result)

        self.assertEqual(result.status_code,
                         302)

    def test_user_logged_in_no_crosswalk(self):
        """ check_crosswalk - User Logged in. No Entry in xwalk """

        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = self.user

        result = check_crosswalk(request)

        # print("No Crosswalk Result:%s" % result.content)

        self.assertContains(result,
                            'Paste the contents of a Blue Button Text File',
                            count=None, status_code=200)

    def test_user_logged_in_crosswalk_no_fhir_id(self):
        """ check_crosswalk - User Logged in. Entry in xwalk. No fhir_id """

        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = self.user
        request.messages = self.messages
        # setattr(request, 'session', 'session')
        # messages = FallbackStorage(request)
        # setattr(request, '_messages', messages)

        xwalk = Crosswalk()
        xwalk.user = request.user
        xwalk.save()

        result = check_crosswalk(request)

        # print("Crosswalk found Result:%s" % result.content)

        self.assertContains(result,
                            'Paste the contents of a Blue Button Text File',
                            count=None, status_code=200)

    # @patch('apps.fhir.testac.views.messages')
    def test_user_logged_in_crosswalk_fhir_id(self):
        """ check_crosswalk - User Logged in. Entry in xwalk with FHIR_ID """

        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = self.user
        request._messages = FakeMessages()
        # setattr(request, 'session', 'session')
        # request.messages = self.messages
        # setattr(request, '_messages', messages)

        xwalk = Crosswalk()
        xwalk.user = self.user
        xwalk.fhir_id = "12345678"
        xwalk.save()

        expected = 'Account is already linked to a FHIR resource.'

        result = check_crosswalk(request)
        result = result

        # print("Crosswalk found "
        #       "with FHIR ID Result:%s" % request._messages.pop)

        self.assertEqual(request._messages.pop, expected)

        # request._messages.pop()

        # self.assertContains(result,
        #                     'Home Page')


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.content = pretty_json(json_data)
            self.json_data = json_data
            self.status_code = status_code
            self.ct = 1

        def json(self):
            return self.json_data

    if "Patient" in args[0]:
        custom_msg = 'Successfully created resource \"Patient/'
        custom_msg += str(randrange(0, 100))
        custom_msg += '/_history/1\" in 14ms'
        result = {"resourceType": "OperationOutcome",
                  "issue": [{"severity": "information",
                             "diagnostics": custom_msg,
                             "code": "informational"}]}

        return MockResponse(result, 201)
    elif "ExplanationOfBenefit" in args[0]:
        custom_msg = 'Successfully created resource \"ExplanationOfBenefit/'
        custom_msg += str(randrange(0, 100))
        custom_msg += '/_history/1\" in 14ms'
        result = {"resourceType": "OperationOutcome",
                  "issue": [{"severity": "information",
                             "diagnostics": custom_msg,
                             "code": "informational"}]}

        return MockResponse(result, 201)

    return MockResponse({}, 404)


def custom_msg():
    custom_msg = 'Successfully created resource \"ExplanationOfBenefit/'
    custom_msg += str(randrange(0, 100))
    custom_msg += '/_history/1\" in 14ms'
    result = {"resourceType": "OperationOutcome",
              "issue": [{"severity": "information",
                         "diagnostics": custom_msg,
                         "code": "informational"}]}

    return result


class TestBBClaimsToEOB(TestCase):
    """ Test conversion of BB_Json to FHIR Patient and EOB """

    @patch('apps.fhir.testac.views.base.requests.post')
    def test_bb_2_patient_eob(self, r_post):
        """ Test writing Patient and EOBs
    http://bluebuttonhapi-test.hhsdevcloud.us/baseDstu2/ExplanationOfBenefit
        """

        r_post.return_value.json.return_value = custom_msg()
        r_post.return_value.status_code = 201
        patient = "Patient/123456789"
        bb_claims = json.loads(SAMPLE_BB_JSON)

        result = bb_to_eob(patient, bb_claims)

        # print("\n:EOB Write Result:%s" % pretty_json(result))
        expected = 5

        self.assertEqual(len(result['resourceId']), expected)
        self.assertEqual(len(result['resource']), expected)
