from __future__ import absolute_import
from __future__ import unicode_literals

import json

from django.core.urlresolvers import reverse

from oauth2_provider.compat import parse_qs, urlparse

from apps.test import BaseApiTest
from ..models import Application


class TestApplicationUpdateView(BaseApiTest):
    def test_update_form_show_allowed_scopes(self):
        """
        """
        read_group = self._create_group('read')
        self._create_capability('Read-Scope', [], read_group)
        write_group = self._create_group('write')
        self._create_capability('Write-Scope', [], write_group)
        # create user and add it to the read group
        user = self._create_user('john', '123456')
        user.groups.add(read_group)
        # create an application
        app = self._create_application('john_app', user=user)
        # render the edit view for the app
        self.client.login(username=user.username, password='123456')
        response = self.client.get(reverse('oauth2_provider:update', args=[app.pk]))
        self.assertContains(response, 'Read-Scope')
        self.assertNotContains(response, 'Write-Scope')


class TestAuthorizationView(BaseApiTest):
    """
    Test the authorization view.
    """
    def test_get_renders_scopes_as_checkboxes(self):
        """
        Test the authorization view renders the form with multiple checkboxes
        to select scopes.
        """
        # create a user
        self._create_user('anna', '123456')
        # create a couple of capabilities
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability_a, capability_b)
        # user logs in
        self.client.login(username='anna', password='123456')
        # get the authorization page
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://example.it',
        }
        response = self.client.get(reverse('oauth2_provider:authorize'), payload)
        self.assertEqual(response.status_code, 200)
        # check form is in context and form initial values are correct
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertEqual(form['redirect_uri'].value(), "http://example.it")
        self.assertEqual(form['scope'].value(), ['capability-a', 'capability-b'])
        self.assertEqual(form['client_id'].value(), application.client_id)
        # check the scopes are rendered as checkboxes and defaulted to checked state
        self.assertContains(
            response,
            '<input checked="checked" id="id_scope_0" name="scope" value="capability-a" type="checkbox">',
            html=True)
        self.assertContains(
            response,
            '<input checked="checked" id="id_scope_1" name="scope" value="capability-b" type="checkbox">',
            html=True)

    def test_post_with_restricted_scopes_issues_token_with_same_scopes(self):
        """
        Test that when user unchecks some of the scopes the token is issued
        with the checked scopes only.
        """
        # create a user
        self._create_user('anna', '123456')
        # create a couple of capabilities
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability_a, capability_b)
        # user logs in
        self.client.login(username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://example.it',
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://example.it',
            'client_id': application.client_id,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))
        # and here we test that only the capability-a scope has been issued
        self.assertEqual(content['scope'], "capability-a")
