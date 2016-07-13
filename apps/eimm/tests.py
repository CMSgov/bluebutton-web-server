from collections import OrderedDict
from unittest import skip
from django.test import TestCase, RequestFactory

from .views import get_fhir_claim
from .utils import split_name
# from ..fhir.bluebutton.utils import pretty_json
# from apps.fhir.bluebutton.utils import pretty_json


class Utils_Test(TestCase):
    """ test eimm utils """

    def test_split_name(self):
        """ Test splitting name into FHIR HumanName """

        in_name = "JOHN A. DOE"

        response = split_name(in_name)
        # result = pretty_json(response)
        expect = OrderedDict([('resourceType', 'HumanName'),
                              ('text', 'JOHN A. DOE'),
                              ('family', ['DOE']),
                              ('given', ['JOHN', 'A.'])])
        expected = """
{
    "resourceType": "HumanName",
    "text": "JOHN A. DOE",
    "family": [
        "DOE"
    ],
    "given": [
        "JOHN",
        "A."
    ]
}
"""
        self.assertEqual(response, expect)

        in_name = "JOHN DOE"
        response = split_name(in_name)
        expected = OrderedDict([('resourceType', 'HumanName'),
                                ('text', 'JOHN DOE'),
                                ('family', ['DOE']),
                                ('given', ['JOHN'])])

        self.assertEqual(response, expected)

        in_name = "JOHN Peter godfrey DOE"
        response = split_name(in_name)
        expected = OrderedDict([('resourceType', 'HumanName'),
                                ('text', 'JOHN Peter godfrey DOE'),
                                ('family', ['DOE']),
                                ('given', ['JOHN', 'Peter', 'godfrey'])])

        self.assertEqual(response, expected)

        in_name = ""
        response = split_name(in_name)
        expected = OrderedDict([('resourceType', 'HumanName')])

        self.assertEqual(response, expected)

        in_name = "JOHN Peter godfrey DOE "
        response = split_name(in_name)
        expected = OrderedDict([('resourceType', 'HumanName'),
                                ('text', 'JOHN Peter godfrey DOE'),
                                ('family', ['DOE']),
                                ('given', ['JOHN', 'Peter', 'godfrey'])])

        # print("\nR:", response)
        # print("\nE:", expected)

        self.assertEqual(response, expected)


class EimmViewsRequestTest(TestCase):

    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()

    @skip
    def test_get_bb_claim(self):
        """
        Pass the blue button claim to backed and get result back

         "system":"CCW_PTA_FACT.CLM_ID",
                        "value":"542882280967266"

        Claims = [
        '542882280967266',  # CCW_PTA_FACT.CLM_ID
        '542612281109054',
        '233464492442129',  # CCW_PDE_FACT.PDE_ID / 263
        '233584489019874',  # CCW_PDE_FACT.PDE_ID / 259
        '',
        ]

        """
        claims = [
            # '542882280967266',  # CCW_PTA_FACT.CLM_ID
            # '542612281109054',
            '233464492442129',  # CCW_PDE_FACT.PDE_ID / 263
            '233584489019874',  # CCW_PDE_FACT.PDE_ID / 259
        ]
        request = {}

        response = {}
        for claim in claims:
            response['text'] = get_fhir_claim(request, claim)
            print("\nclaim:", claim)
            print('\nRT:', response['text'])

            self.assertEqual(response['text']['claimIdentifier'], claim)


    def test_unique_keys(self):
        """ Pass searched claims to unique_keys """

        input_list = [
            {'identifier': '5',
             'provider': 'Practitioner/6',
             'claimIdentifier': '542882280967266',
             'claimNumber': '542882280967266',
             'patient': 'Patient/1',
             'timingPeriod': OrderedDict([('start',
                                           '2008-05-03T00:00:00+00:00'),
                                          ('end',
                                           '2008-05-03T00:00:00+00:00')]),
             'found': True},

        ]

        print(input_list)
