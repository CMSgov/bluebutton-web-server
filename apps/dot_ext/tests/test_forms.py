from apps.test import BaseApiTest
from apps.dot_ext.forms import CustomRegisterApplicationForm
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings


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

        # Test form with valid description.
        data = {'description': 'Testing short description here!'}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertEqual(form.errors.get('description'), None)

        # Test form with description over 1000 characters.
        data = {'description': 'T' * 1001}
        form = CustomRegisterApplicationForm(user, data)
        form.is_valid()
        self.assertNotEqual(form.errors.get('description'), None)

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
