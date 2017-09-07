#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: test_mock
Created: 7/20/16 4:08 PM

File created by: ''
"""
import json
import unittest
try:
    # python 3 - Mock is now a standard module in unittest
    from unittest.mock import patch
except ImportError:
    # python 2 - Mock needs to be pip installed
    from mock import patch   # NOQA

from collections import OrderedDict
from django.test import RequestFactory

from django.conf import settings

from apps.fhir.bluebutton.utils import (post_process_request,
                                        build_output_dict,
                                        request_call,
                                        pretty_json,
                                        get_resourcerouter)

from apps.fhir.server.models import ResourceRouter

from .data_conformance import CONFORMANCE


class UtilsTestCase(unittest.TestCase):
    """ testing mock pass of request data """

    fixtures = ['fhir_bluebutton_test_rt.json']

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.resrtr = ResourceRouter.objects.create(
            name="The main server [Default]",
            server_address="https://fhir.backend.bluebutton.hhsdevcloud.us",
            server_path="/",
            server_release="baseDstu3/",
            server_search_expiry=1800,
            fhir_url="https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/",
            shard_by="Patient",
            client_auth=True,
            cert_file="/ca.cert.pem",
            key_file="./ca.key.nocrypt.pem",
            server_verify=False)

        self.factory = RequestFactory()

    def test_post_process_request_json(self):
        """ Replace urls in list with host_path in a text string """

        # FHIR_SERVER_CONF = {
        #   "SERVER": "http://fhir.bbonfhir.com/",
        #   "PATH": "fhir-p/",
        #   "RELEASE": "baseDstu2/",
        #   "REWRITE_FROM": "http://ec2-52-4-198-86.compute-1.amazonaws.com" \
        #                   ":8080/baseDstu2",
        #   "REWRITE_TO": "http://localhost:8000/bluebutton/fhir/v1"}

        """
        text_out = mask_list_with_host(request,
                                   host_path,
                                   r_text,
                                   rewrite_url_list)
        """

        assert_msg = """
         Test 1: No text to replace. No changes
         """
        fmt = "json"

        rr_id = self.resrtr.id
        print("\nResRtr-testfetch:%s=%s\n" % (rr_id, self.resrtr))
        rr = get_resourcerouter()

        print("\nRR-testfetch:%s\n" % rr)

        if settings.RUNNING_PYTHON2:
            default_url = rr.server_address.encode('utf-8')
        else:
            default_url = rr.server_address

        request = self.factory.get('/cmsblue/fhir/v1/Patient')

        print("\nDefault_url:%s\n" % default_url)

        input_text = 'dddd anything '
        input_text += default_url
        input_text += ' will get replaced more stuff '
        input_text += 'http://www.example.com:8000 and '
        input_text += 'http://example.com:8000/ okay'

        host_path = 'http://www.replaced.com'
        r_text = '{}'
        rewrite_url_list = [default_url,
                            'http://www.example.com:8000',
                            'http://example.com']

        if default_url.endswith("/"):
            pass
        else:
            rewrite_url_list.append(default_url + '/')

        result = post_process_request(request,
                                      fmt,
                                      host_path,
                                      r_text,
                                      rewrite_url_list)

        # expected = ''
        expected = OrderedDict()
        self.assertEqual(result, expected, assert_msg)

        assert_msg = """
            Test 2: No text to replace with. Only replace
            FHIR_SERVER_CONF.REWRITE_FROM changes
        """

        input_text = '{"next": "dddd anything '
        input_text += default_url
        input_text += ' will get replaced more stuff '
        input_text += 'http://www.example.com:8000 and '
        input_text += 'http://example.com:8000/ okay"}'

        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        r_text = input_text
        rewrite_url_list = []

        result = post_process_request(request,
                                      fmt,
                                      host_path,
                                      r_text,
                                      rewrite_url_list)
        expected = json.loads(input_text,
                              object_pairs_hook=OrderedDict)
        # expected = input_text

        self.assertEqual(result, expected, assert_msg)

        assert_msg = """
        Test 3: Replace text removing slash from end of replaced text
        """

        input_text = '{"next": "dddd anything '
        input_text += default_url
        input_text += ' will get replaced more stuff '
        input_text += 'http://www.example.com:8000 and '
        input_text += 'http://example.com:8000/ okay"}'

        request = self.factory.get('/cmsblue/fhir/v1/Patient')

        host_path = 'http://www.replaced.com'
        r_text = input_text
        rewrite_url_list = [default_url,
                            'http://www.example.com:8000',
                            'http://example.com']

        if default_url.endswith("/"):
            pass
        else:
            rewrite_url_list.append(default_url + '/')

        result = post_process_request(request,
                                      fmt,
                                      host_path,
                                      r_text,
                                      rewrite_url_list)

        expected_text = '{"next": "dddd anything http://www.replaced.com ' \
                        'will get replaced ' \
                        'more stuff http://www.replaced.com and ' \
                        'http://www.replaced.com:8000/ okay"}'
        expected = json.loads(expected_text,
                              object_pairs_hook=OrderedDict)

        # print("\n\n\nResponse:", result)
        # print("\n\n\nExpected:", expected)

        self.assertEqual(result, expected, assert_msg)

        assert_msg = """
                        Test 4: Replace text
        """

        input_text = '{"next": "dddd anything '
        input_text += default_url
        input_text += ' will get replaced more stuff '
        input_text += 'http://www.example.com:8000 and '
        input_text += 'http://example.com:8000/ okay"}'

        request = self.factory.get('/cmsblue/fhir/v1/Patient')

        rewrite_url_list = [default_url,
                            'http://www.example.com:8000',
                            'http://example.com']

        if default_url.endswith("/"):
            pass
        else:
            rewrite_url_list.append(default_url + '/')

        result = post_process_request(request,
                                      fmt,
                                      host_path,
                                      r_text,
                                      rewrite_url_list)

        expected_text = '{"next": "dddd anything http://www.replaced.com ' \
                        'will get replaced ' \
                        'more stuff http://www.replaced.com and ' \
                        'http://www.replaced.com:8000/ okay"}'
        expected = json.loads(expected_text,
                              object_pairs_hook=OrderedDict)

        self.assertEqual(result, expected, assert_msg)

    def test_post_process_request_xml(self):
        """ Replace urls in list with host_path in a text string """

        # FHIR_SERVER_CONF = {
        #   "SERVER": "http://fhir.bbonfhir.com/",
        #   "PATH": "fhir-p/",
        #   "RELEASE": "baseDstu2/",
        #   "REWRITE_FROM": "http://ec2-52-4-198-86.compute-1.amazonaws.com" \
        #                   ":8080/baseDstu2",
        #   "REWRITE_TO": "http://localhost:8000/bluebutton/fhir/v1"}

        """
        text_out = mask_list_with_host(request,
                                   host_path,
                                   r_text,
                                   rewrite_url_list)
        """

        assert_msg = """
         Test 1: No text to replace. No changes. fmt = xml
         """
        fmt = "xml"

        request = self.factory.get('/cmsblue/fhir/v1/Patient')

        # rr_id = self.resrtr.id
        # print("\nResRtr-testfetch:%s=%s\n" % (rr_id, self.resrtr))
        rr = get_resourcerouter()

        # print("\nRR-testfetch:%s\n" % rr)

        if settings.RUNNING_PYTHON2:
            default_url = rr.server_address.encode('utf-8')
        else:
            default_url = rr.server_address

        # print("\n\n", default_url)

        input_text = 'dddd anything '
        input_text += default_url
        input_text += ' will get replaced more stuff '
        input_text += 'http://www.example.com:8000 and '
        input_text += 'http://example.com:8000/ okay'

        host_path = 'http://www.replaced.com'
        r_text = ''
        rewrite_url_list = [default_url,
                            'http://www.example.com:8000',
                            'http://example.com']

        if default_url.endswith("/"):
            pass
        else:
            rewrite_url_list.append(default_url + '/')

        result = post_process_request(request,
                                      fmt,
                                      host_path,
                                      r_text,
                                      rewrite_url_list)

        expected = ''
        # expected = OrderedDict()
        self.assertEqual(result, expected, assert_msg)

        assert_msg = """
            Test 2: No text to replace with. Only replace
            FHIR_SERVER_CONF.REWRITE_FROM changes
        """

        input_text = '<next> "dddd anything '
        input_text += default_url
        input_text += ' will get replaced more stuff '
        input_text += 'http://www.example.com:8000 and '
        input_text += 'http://example.com:8000/ okay"</next>'

        request = self.factory.get('/cmsblue/fhir/v1/Patient')
        r_text = input_text
        rewrite_url_list = []

        result = post_process_request(request,
                                      fmt,
                                      host_path,
                                      r_text,
                                      rewrite_url_list)
        # expected = json.loads(input_text,
        #                       object_pairs_hook=OrderedDict)
        expected = input_text

        self.assertEqual(result, expected, assert_msg)

        assert_msg = """
        Test 3: Replace text removing slash from end of replaced text
        """

        input_text = '<next> "dddd anything '
        input_text += default_url
        input_text += ' will get replaced more stuff '
        input_text += 'http://www.example.com:8000 and '
        input_text += 'http://example.com:8000/ okay"</next>'

        request = self.factory.get('/cmsblue/fhir/v1/Patient')

        host_path = 'http://www.replaced.com'
        r_text = input_text
        rewrite_url_list = [default_url,
                            'http://www.example.com:8000',
                            'http://example.com']

        if default_url.endswith("/"):
            pass
        else:
            rewrite_url_list.append(default_url + '/')

        result = post_process_request(request,
                                      fmt,
                                      host_path,
                                      r_text,
                                      rewrite_url_list)

        expected_text = '<next> "dddd anything http://www.replaced.com ' \
                        'will get replaced ' \
                        'more stuff http://www.replaced.com and ' \
                        'http://www.replaced.com:8000/ okay"</next>'
        # expected = json.loads(expected_text,
        #                       object_pairs_hook=OrderedDict)

        # print("\nRewrite_list:%s" % rewrite_url_list)
        # print("\n\n\nResponse:", result)
        # print("\n\n\nExpected:", expected_text)

        self.assertEqual(result, expected_text, assert_msg)

        assert_msg = """
                        Test 4: Replace text
        """

        input_text = '<next> "dddd anything '
        input_text += default_url
        input_text += ' will get replaced more stuff '
        input_text += 'http://www.example.com:8000 and '
        input_text += 'http://example.com:8000/ okay"</next>'

        r_text = input_text

        request = self.factory.get('/cmsblue/fhir/v1/Patient')

        rewrite_url_list = [default_url,
                            'http://www.example.com:8000',
                            'http://example.com']

        if default_url.endswith("/"):
            pass
        else:
            rewrite_url_list.append(default_url + '/')

        result = post_process_request(request,
                                      fmt,
                                      host_path,
                                      r_text,
                                      rewrite_url_list)

        expected_text = '<next> "dddd anything http://www.replaced.com ' \
                        'will get replaced ' \
                        'more stuff http://www.replaced.com and ' \
                        'http://www.replaced.com:8000/ okay"</next>'
        # expected = json.loads(expected_text,
        #                       object_pairs_hook=OrderedDict)

        self.assertEqual(result, expected_text, assert_msg)

    def test_build_output_dict(self):
        """ Build the Output Dict """

        request = self.factory.get('/cmsblue/fhir/v1/Patient')

        assert_msg = """
            1. Send the data - simple test
        """

        fmt = "json"
        resource_type = "Patient"
        key = "11223344"
        vid = "1"
        interaction_type = "search"
        expected_text = '{"next": "dddd anything http://www.replaced.com ' \
                        'will get replaced ' \
                        'more stuff http://www.replaced.com and ' \
                        'http://www.replaced.com:8000/ okay"}'
        text_out = json.loads(expected_text,
                              object_pairs_hook=OrderedDict)
        od = OrderedDict()

        resp = build_output_dict(request,
                                 od,
                                 resource_type,
                                 key,
                                 vid,
                                 interaction_type,
                                 fmt,
                                 text_out)

        wanted = OrderedDict()
        wanted["resource_type"] = resource_type
        wanted["id"] = key
        wanted["vid"] = vid
        wanted["bundle"] = text_out

        # print("\nRESP:%s" % resp)
        # print("\nEXPC:%s" % wanted)

        # expected = OrderedDict()

        self.assertEqual(resp, wanted, assert_msg)

        assert_msg = """
            2. Send the data - no vid
        """

        fmt = "json"
        resource_type = "Patient"
        key = "11223344"
        vid = None
        interaction_type = "search"
        expected_text = '{"next": "dddd anything http://www.replaced.com ' \
                        'will get replaced ' \
                        'more stuff http://www.replaced.com and ' \
                        'http://www.replaced.com:8000/ okay"}'
        text_out = json.loads(expected_text,
                              object_pairs_hook=OrderedDict)
        od = OrderedDict()

        resp = build_output_dict(request,
                                 od,
                                 resource_type,
                                 key,
                                 vid,
                                 interaction_type,
                                 fmt,
                                 text_out)

        wanted = OrderedDict()
        wanted["resource_type"] = resource_type
        wanted["id"] = key
        # wanted["vid"] = vid
        wanted["bundle"] = text_out

        # print("\nRESP:%s" % resp)
        # print("\nEXPC:%s" % wanted)

        self.assertEqual(resp, wanted, assert_msg)


class RequestCallMockTest(unittest.TestCase):
    """ Testing patch to requests.get in request_call """

    fixtures = ['fhir_bluebutton_test_rt.json']

    def setUp(self):
        # Setup the RequestFactory
        self.resrtr = ResourceRouter.objects.create(
            name="The main server [Default]",
            server_address="https://fhir.backend.bluebutton.hhsdevcloud.us",
            server_path="/",
            server_release="baseDstu3/",
            server_search_expiry=1800,
            fhir_url="https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/",
            shard_by="Patient",
            client_auth=True,
            cert_file="/ca.cert.pem",
            key_file="./ca.key.nocrypt.pem",
            server_verify=False)
        self.factory = RequestFactory()

    @patch('apps.fhir.bluebutton.utils.requests')
    def test_fetch(self, mock_requests):

        # rr_id = self.resrtr.id
        # print("\nResRtr-testfetch:%s=%s\n" % (rr_id, self.resrtr))

        # rr = get_resourcerouter()
        # print("\nRR-testfetch:%s\n" % rr)

        request = self.factory.get('http://someurl.com/test.text')
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.text = CONFORMANCE
        mock_requests.get.return_value.json = pretty_json({"field": "My text "
                                                                    "is here"
                                                                    "!!!!"})

        resp = request_call(request,
                            "http://someurl.com/test.text",
                            cx=None)

        # print("\nResp.text:\n%s" % resp.text)
        # print("\nResp.json:\n%s" % resp.json)

        self.assertEqual(resp._text[:100],
                         CONFORMANCE[:100])
