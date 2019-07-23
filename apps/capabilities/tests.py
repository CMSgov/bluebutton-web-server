import json
from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import Group
from .models import ProtectedCapability

from .permissions import TokenHasProtectedCapability


class SimpleRequest(object):
    method = ""
    path = ""


class TestTokenHasProtectedCapability(TestCase):
    def setUp(self):
        g = Group.objects.create(name="test")
        ProtectedCapability.objects.create(
            title="test capability",
            slug="i'm really the scope :facepalm:",
            group=g,
            protected_resources=json.dumps([["GET", "/path"]]),
        )
        ProtectedCapability.objects.create(
            title="unused capability",
            slug="unused",
            group=g,
            protected_resources=json.dumps([["POST", "/path"]]),
        )

    def test_request_is_protected(self):
        request = SimpleRequest()
        request.method = "GET"
        request.path = "/path"

        perm = TokenHasProtectedCapability()
        scopes = perm.get_scopes(request, None)
        self.assertEqual(scopes, ["i'm really the scope :facepalm:"])

    def test_protected_path_not_registered(self):
        request = SimpleRequest()
        request.method = "GET"
        request.path = "/should-be-protected"

        perm = TokenHasProtectedCapability()
        with self.assertRaises(ImproperlyConfigured):
            perm.get_scopes(request, None)

    def test_protected_path_method_not_registered(self):
        request = SimpleRequest()
        request.method = "PUT"
        request.path = "/path"

        perm = TokenHasProtectedCapability()
        with self.assertRaises(ImproperlyConfigured):
            perm.get_scopes(request, None)
