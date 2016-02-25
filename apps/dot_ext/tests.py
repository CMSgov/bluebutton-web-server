from __future__ import absolute_import
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase

from ..test import BaseApiTest


class TestApplicationUpdateView(BaseApiTest):
    def test_update_form_show_allowed_scopes(self):
        """
        """
        read_group = self._create_group('read')
        read_capability = self._create_capability('Read-Scope', [], read_group)
        write_group = self._create_group('write')
        write_capability = self._create_capability('Write-Scope', [], write_group)
        # create user and add it to the read group
        user = self._create_user('john', '123456')
        user.groups.add(read_group)
        # create an application
        app = self._create_application('john_app', user=user)
        # render the edit view for the app
        self.client.login(username=user.username, password='123456')
        response = self.client.get(reverse('dote_update', args=[app.pk]))
        self.assertContains(response, 'Read-Scope')
        self.assertNotContains(response, 'Write-Scope')


class TestApplicationModel(BaseApiTest):
    def test_allow_resource_method_return_false_for_forbidden_resource(self):
        # create an empty capability
        capability = self._create_capability('Capability', [])
        # create an application with the capability
        app = self._create_application('john_app', capability=capability)
        self.assertFalse(app.allow_resource('GET', '/api/foo/'))

    def test_allow_resource_method_return_true_for_allowed_resource(self):
        # create an empty capability
        capability = self._create_capability('Capability', [['GET', '/api/foo/']])
        # create an application with the capability
        app = self._create_application('john_app', capability=capability)
        self.assertTrue(app.allow_resource('GET', '/api/foo/'))
