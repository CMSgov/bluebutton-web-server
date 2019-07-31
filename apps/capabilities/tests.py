import json
from django.test import TestCase
from django.contrib.auth.models import Group
from waffle.testutils import override_switch

from .models import ProtectedCapability

from .permissions import TokenHasProtectedCapability


class SimpleToken(object):
    scope = ""


class SimpleRequest(object):
    method = ""
    path = ""

    def __init__(self, scope=""):
        self.auth = SimpleToken()
        self.auth.scope = scope


@override_switch('require-scopes', active=True)
class TestTokenHasProtectedCapability(TestCase):
    def setUp(self):
        g = Group.objects.create(name="test")
        ProtectedCapability.objects.create(
            title="test capability",
            slug="scope",
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
        request = SimpleRequest("scope")
        request.method = "GET"
        request.path = "/path"

        perm = TokenHasProtectedCapability()
        self.assertTrue(perm.has_permission(request, None))

    def test_protected_path_not_allowed(self):
        request = SimpleRequest("unused")
        request.method = "GET"
        request.path = "/path"

        perm = TokenHasProtectedCapability()
        self.assertFalse(perm.has_permission(request, None))

    def test_protected_path_no_scopes(self):
        request = SimpleRequest()
        request.method = "GET"
        request.path = "/path"

        perm = TokenHasProtectedCapability()
        self.assertFalse(perm.has_permission(request, None))
