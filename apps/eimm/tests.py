# from django.test import TestCase

# Create your tests here.
from collections import OrderedDict

from django.test import TestCase

from .utils import split_name
from apps.fhir.bluebutton.utils import pretty_json

class Utils_Test(TestCase):
    """ test eimm utils """

    def test_split_name(self):
        """ Test splitting name into FHIR HumanName """

        in_name = "JOHN A. DOE"

        response = split_name(in_name)
        result = pretty_json(response)
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
                              ('text', 'JOHN Peter Godfrey DOE'),
                              ('family', ['DOE']),
                              ('given', ['JOHN', 'Peter', 'godfrey'])])



