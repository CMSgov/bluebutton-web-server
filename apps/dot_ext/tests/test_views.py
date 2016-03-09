from __future__ import absolute_import
from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from ...test import BaseApiTest


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
        response = self.client.get(reverse('oauth2_provider:update', args=[app.pk]))
        self.assertContains(response, 'Read-Scope')
        self.assertNotContains(response, 'Write-Scope')
