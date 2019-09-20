from django.urls import reverse

from apps.test import BaseApiTest


class TestDOTTemplates(BaseApiTest):
    def test_application_list_template_override(self):
        """
        Test that the application list template is overridden.
        """
        self._create_user('john', '123456')
        self.client.login(username='john', password='123456')
        response = self.client.get(reverse("oauth2_provider:list"))
        self.assertEquals(response.status_code, 200)

    def test_application_detail_template_override(self):
        """
        Test that the application detail is overridden.
        """
        user = self._create_user('john', '123456')
        self.client.login(username='john', password='123456')
        # create an application
        app = self._create_application('john_app', user=user)
        response = self.client.get(reverse("oauth2_provider:detail", args=[app.pk]))
        self.assertEquals(response.status_code, 200)

    def test_application_confirm_delete_template_override(self):
        """
        Test that the application confirm_delete is overridden.
        """
        user = self._create_user('john', '123456')
        self.client.login(username='john', password='123456')
        # create an application
        app = self._create_application('john_app', user=user)
        response = self.client.get(reverse("oauth2_provider:delete", args=[app.pk]))
        self.assertEquals(response.status_code, 200)

    def test_application_update_template_override(self):
        """
        Test that the application update is overridden.
        """
        user = self._create_user('john', '123456')
        self.client.login(username='john', password='123456')
        # create an application
        app = self._create_application('john_app', user=user)
        response = self.client.get(reverse("oauth2_provider:update", args=[app.pk]))
        self.assertEquals(response.status_code, 200)

    def test_application_registration_template_override(self):
        """
        Test that the application registration is overridden.
        """
        self._create_user('john', '123456')
        self.client.login(username='john', password='123456')
        response = self.client.get(reverse("oauth2_provider:register"))
        self.assertEquals(response.status_code, 200)
