import json

from django.contrib.auth.models import Group
from django.test import TestCase
from waffle.testutils import override_switch

from apps.capabilities.permissions import BBCapabilitiesPermissionTokenScopeMissingException
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
class TestTokenHasProtectedCapabilityScopesSwitchTrue(TestCase):
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

    def test_protected_path_token_has_no_scope_attribute(self):
        # BB2-237: Test replacement of ASSERT in apps/capabilities/permissions.py
        # Fake request with auth
        class FakeRequest:
            def __init__(self, auth):
                self.auth = auth

        # Fake auth/token
        class FakeAuth:
            def __init__(self, scope):
                self.no_scope = scope

        request = FakeRequest(FakeAuth("testing"))

        perm = TokenHasProtectedCapability()
        with self.assertRaisesRegexp(BBCapabilitiesPermissionTokenScopeMissingException, "TokenHasScope requires.*"):
            perm.has_permission(request, None)


@override_switch('require-scopes', active=False)
class TestTokenHasProtectedCapabilityScopesSwitchFalse(TestCase):
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
        # Note that this is allowed with the scopes switch False/Off
        self.assertTrue(perm.has_permission(request, None))

    def test_protected_path_no_scopes(self):
        request = SimpleRequest()
        request.method = "GET"
        request.path = "/path"

        perm = TokenHasProtectedCapability()
        # Note that this is allowed with the scopes switch False/Off
        self.assertTrue(perm.has_permission(request, None))
