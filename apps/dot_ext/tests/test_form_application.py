from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from PIL import Image
from io import BytesIO

from apps.test import BaseApiTest
from apps.dot_ext.forms import CustomRegisterApplicationForm
from apps.dot_ext.admin import CustomAdminApplicationForm


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

        form = CustomAdminApplicationForm(data)
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

        # Test form with website_uri valid URI.
        data = {'website_uri': 'https://www.example.org'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('website_uri'), None)

        # Test form with website_uri in-valid URI.
        data = {'website_uri': 'xyzs:/www.example.org'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertNotEqual(form.errors.get('website_uri'), None)

        # Test form with website_uri EMPTY URI is OK.
        data = {'website_uri': ''}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('website_uri'), None)

        # Test form with empty description.
        data = {'description': ''}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('description'), None)

        form = CustomAdminApplicationForm(data)
        form.is_valid()
        self.assertEqual(form.errors.get('description'), None)

        # Test form with valid description.
        data = {'description': 'Testing short description here!'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('description'), None)

        form = CustomAdminApplicationForm(data)
        form.is_valid()
        self.assertEqual(form.errors.get('description'), None)

        # Test form with description over 1000 characters.
        data = {'description': 'T' * 1001}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertNotEqual(form.errors.get('description'), None)

        form = CustomAdminApplicationForm(data)
        form.is_valid()
        self.assertEqual(form.errors.get('description'), None)

        # Test form with description exactly 1000 characters.
        data = {'description': 'T' * 1000}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('description'), None)

        # Test form with HTML tags in the description.
        data = {'description': '<b>Test</b> <button>Test</button> a <span>Test</span>'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertNotEqual(form.errors.get('description'), None)

        form = CustomAdminApplicationForm(data)
        form.is_valid()
        self.assertEqual(form.errors.get('description'), None)

        # Testing valid logo_image with max dimensions
        file = BytesIO()
        image = Image.new('RGB', size=(int(settings.APP_LOGO_WIDTH_MAX),
                          int(settings.APP_LOGO_HEIGHT_MAX)), color='red')
        image.save(file, 'jpeg')
        file.seek(0)
        image = InMemoryUploadedFile(
            file, None, 'test.jpg', 'image/jpeg', len(file.getvalue()), None
        )
        data = {}
        files = {'logo_image': image}
        form = CustomRegisterApplicationForm(user, data, files)
        form.is_valid()
        self.assertEqual(form.errors.get('logo_image'), None)

        # Testing logo_image exceeding max width
        file = BytesIO()
        image = Image.new('RGB', size=(int(settings.APP_LOGO_WIDTH_MAX) + 1,
                          int(settings.APP_LOGO_HEIGHT_MAX)), color='red')
        image.save(file, 'jpeg')
        file.seek(0)
        image = InMemoryUploadedFile(
            file, None, 'test.jpg', 'image/jpeg', len(file.getvalue()), None
        )
        data = {}
        files = {'logo_image': image}
        form = CustomRegisterApplicationForm(user, data, files)
        form.is_valid()
        self.assertNotEqual(form.errors.get('logo_image'), None)

        form = CustomAdminApplicationForm(data, files)
        form.is_valid()
        self.assertNotEqual(form.errors.get('logo_image'), None)

        # Testing logo_image exceeding max height
        file = BytesIO()
        image = Image.new('RGB', size=(int(settings.APP_LOGO_WIDTH_MAX),
                          int(settings.APP_LOGO_HEIGHT_MAX) + 1), color='red')
        image.save(file, 'jpeg')
        file.seek(0)
        image = InMemoryUploadedFile(
            file, None, 'test.jpg', 'image/jpeg', len(file.getvalue()), None
        )
        data = {}
        files = {'logo_image': image}
        form = CustomRegisterApplicationForm(user, data, files)
        form.is_valid()
        self.assertNotEqual(form.errors.get('logo_image'), None)

        form = CustomAdminApplicationForm(data, files)
        form.is_valid()
        self.assertNotEqual(form.errors.get('logo_image'), None)

        # Testing logo_image not JPEG type
        file = BytesIO()
        image = Image.new('RGB', size=(50, 50), color='red')
        image.save(file, 'png')
        file.seek(0)
        image = InMemoryUploadedFile(
            file, None, 'test.png', 'image/png', len(file.getvalue()), None
        )
        data = {}
        files = {'logo_image': image}
        form = CustomRegisterApplicationForm(user, data, files)
        form.is_valid()
        self.assertNotEqual(form.errors.get('logo_image'), None)
        form = CustomAdminApplicationForm(data, files)
        form.is_valid()
        self.assertNotEqual(form.errors.get('logo_image'), None)

        # Test require_demographic_scopes value True
        data = {'require_demographic_scopes': True}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('require_demographic_scopes'), None)

        # Test require_demographic_scopes value False
        data = {'require_demographic_scopes': False}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('require_demographic_scopes'), None)

        # Test require_demographic_scopes invalid value
        data = {'require_demographic_scopes': None}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertNotEqual(form.errors.get('require_demographic_scopes'), None)

    def test_create_applications_with_logo(self):
        """
        regression test: BB2-66: Fix-logo-display-in-Published-Applications-API
        """
        greetings_group = self._create_group('Greetings')
        # create user and add it to the read group
        user = self._create_user('hello.world', '123hello456')
        user.groups.add(greetings_group)
        # create APP1 and APP2 with logo_image and other required and optional fields
        # persist application object through CustomRegisterApplicationForm
        form_app1 = self.create_app_form_with_logo(app_name='BB2-66-APP-1', user=user,
                                                   file_name='test_app1_logo.jpg', color='red')
        self.assertFalse(form_app1.errors, "There are error(s) in the new app register form.")

        form_app2 = self.create_app_form_with_logo(app_name='BB2-66-APP-2', user=user,
                                                   file_name='test_app2_logo.jpg', color='blue')
        self.assertFalse(form_app2.errors, "There are error(s) in the new app register form.")

        # check APP1 and APP2 are saved in django and have correct path pointing to
        # logo image files, no image overriden
        app_obj1 = self._get_user_application(user.username, 'BB2-66-APP-1')
        app_obj2 = self._get_user_application(user.username, 'BB2-66-APP-2')
        self.assertIsNotNone(app_obj1.logo_uri)
        self.assertTrue(app_obj1.logo_uri)
        self.assertIsNotNone(app_obj2.logo_uri)
        self.assertTrue(app_obj2.logo_uri)
        self.assertNotEqual(app_obj1.logo_uri, app_obj2.logo_uri)

    def create_app_form_with_logo(self, app_name=None, user=None, file_name=None, color=None):
        """
        helper to generate a jpg as logo image
        """
        self.assertIsNotNone(user)
        self.assertIsNotNone(app_name)
        self.assertIsNotNone(file_name)
        self.assertIsNotNone(color)
        logo_file = BytesIO()
        image = Image.new('RGB', size=(int(settings.APP_LOGO_WIDTH_MAX),
                          int(settings.APP_LOGO_HEIGHT_MAX)), color=color)
        image.save(logo_file, 'jpeg')
        logo_file.seek(0)
        image = InMemoryUploadedFile(
            logo_file, None, file_name, 'image/jpeg', len(logo_file.getvalue()), None
        )
        app_fields = {'name': app_name,
                      'client_type': 'confidential',
                      'authorization_grant_type': 'authorization-code',
                      'redirect_uris': 'http://localhost:8000/social-auth/complete/oauth2io/',
                      'logo_uri': '',
                      'logo_image': image,
                      'website_uri': '',
                      'description': 'User:' + user.username + ', registered app: ' + app_name,
                      'policy_uri': '',
                      'tos_uri': '',
                      'support_email': '',
                      'support_phone_number': '',
                      'contacts': '',
                      'require_demographic_scopes': True,
                      'agree': True}
        files = {'logo_image': image}
        form = CustomRegisterApplicationForm(user, app_fields, files)
        app_model = form.instance
        app_model.user = user
        # to simulate the context in BB2 runtime when
        # a new CustomRegisterApplicationForm instance is saved
        # as BB2 admin user added a new app with logo
        form.save(commit=False)
        return form
