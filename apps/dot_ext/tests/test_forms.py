from apps.test import BaseApiTest
from apps.dot_ext.forms import CustomRegisterApplicationForm


class TestRegisterApplicationForm(BaseApiTest):
    def test_update_form_edit(self):
        """
        """
        read_group = self._create_group('read')
        self._create_capability('Read-Scope', [], read_group)
        # create user and add it to the read group
        user = self._create_user('john', '123456')
        user.groups.add(read_group)
        # create an application
        self._create_application('john_app', user=user)

        # Test form with exact app name has error
        data = {'name': 'john_app'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertNotEqual(form.errors.get('name'), None)

        # Test form with same app name and Uppercase has error
        data = {'name': 'John_App'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertNotEqual(form.errors.get('name'), None)

        # Test form with different app name is OK
        data = {'name': 'Dave_app'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('name'), None)

        # Test form with empty app name has error.
        data = {'name': ''}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertNotEqual(form.errors.get('name'), None)

        # Test form with client_url valid URI.
        data = {'client_uri': 'https://www.example.org'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('client_uri'), None)

        # Test form with client_url in-valid URI.
        data = {'client_uri': 'xyzs:/www.example.org'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertNotEqual(form.errors.get('client_uri'), None)

        # Test form with client_url EMPTY URI is OK.
        data = {'client_uri': ''}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('client_uri'), None)
