from io import BytesIO

import pytest
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management import call_command
from PIL import Image

from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.constants import BENE_PERSONAL_INFO_SCOPES
from apps.dot_ext.forms import (
    CreateApplicationForm,
    CustomRegisterApplicationForm,
    EditApplicationForm,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'application_form, data, field, error_text_expected, should_pass',
    [
        # Test form with exact app name has error
        (
            CustomRegisterApplicationForm,
            {'name': 'john_app'},
            'name',
            'is already in use with another app.',
            False,
        ),
        (
            CreateApplicationForm,
            {'name': 'john_app'},
            'name',
            'is already in use with another app.',
            False,
        ),
        (
            EditApplicationForm,
            {'name': 'john_app'},
            'name',
            'is already in use with another app.',
            False,
        ),
        # Test form with same app name and uppercase has error
        (
            CustomRegisterApplicationForm,
            {'name': 'John_App'},
            'name',
            'is already in use with another app.',
            False,
        ),
        (
            CreateApplicationForm,
            {'name': 'John_App'},
            'name',
            'is already in use with another app.',
            False,
        ),
        (
            EditApplicationForm,
            {'name': 'John_App'},
            'name',
            'is already in use with another app.',
            False,
        ),
        # Test form with different app name is successful
        (
            CustomRegisterApplicationForm,
            {'name': 'Dave_App'},
            'name',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'name': 'Dave_App'},
            'name',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'name': 'Dave_App'},
            'name',
            None,
            True,
        ),
        # Test form with no app name has error
        (
            CustomRegisterApplicationForm,
            {'name': ''},
            'name',
            'Application name is required.',
            False,
        ),
        (
            CreateApplicationForm,
            {'name': ''},
            'name',
            'This field is required.',
            False,
        ),
        (
            EditApplicationForm,
            {'name': ''},
            'name',
            'This field is required.',
            False,
        ),
        # Test form with invalid app name has error (app name contains non-ascii char(s)).
        (
            CustomRegisterApplicationForm,
            {'name': '🚀'},
            'name',
            'Invalid character(s) in application name',
            False,
        ),
        (
            CreateApplicationForm,
            {'name': '🚀'},
            'name',
            'Invalid character(s) in application name',
            False,
        ),
        (
            EditApplicationForm,
            {'name': '🚀'},
            'name',
            'Invalid character(s) in application name',
            False,
        ),
        # Test form with invalid app name has error (app name contains en dashes).
        (
            CustomRegisterApplicationForm,
            {'name': 'BB2–2993–en–dash'},
            'name',
            'Invalid character(s) in application name',
            False,
        ),
        (
            CreateApplicationForm,
            {'name': 'BB2–2993–en–dash'},
            'name',
            'Invalid character(s) in application name',
            False,
        ),
        (
            EditApplicationForm,
            {'name': 'BB2–2993–en–dash'},
            'name',
            'Invalid character(s) in application name',
            False,
        ),
        # Test form with website_uri valid URI.
        (
            CustomRegisterApplicationForm,
            {'website_uri': 'https://www.example.org'},
            'website_uri',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'website_uri': 'https://www.example.org'},
            'website_uri',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'website_uri': 'https://www.example.org'},
            'website_uri',
            None,
            True,
        ),
        # Test form with website_uri invalid URI.
        (
            CustomRegisterApplicationForm,
            {'website_uri': 'xyzs:/www.example.org'},
            'website_uri',
            'Enter a valid URL',
            False,
        ),
        (
            CreateApplicationForm,
            {'website_uri': 'xyzs:/www.example.org'},
            'website_uri',
            'Enter a valid URL',
            False,
        ),
        (
            EditApplicationForm,
            {'website_uri': 'xyzs:/www.example.org'},
            'website_uri',
            'Enter a valid URL',
            False,
        ),
        # Test form with empty website_uri should pass.
        (
            CustomRegisterApplicationForm,
            {'website_uri': ''},
            'website_uri',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'website_uri': ''},
            'website_uri',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'website_uri': ''},
            'website_uri',
            None,
            True,
        ),
        # Test form with jwks_uri valid URI.
        (
            CustomRegisterApplicationForm,
            {'jwks_uri': 'https://www.example.org'},
            'jwks_uri',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'jwks_uri': 'https://www.example.org'},
            'jwks_uri',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'jwks_uri': 'https://www.example.org'},
            'jwks_uri',
            None,
            True,
        ),
        # Test form with jwks_uri invalid URI.
        (
            CustomRegisterApplicationForm,
            {'jwks_uri': 'xyzs:/www.example.org'},
            'jwks_uri',
            'Enter a valid URL',
            False,
        ),
        (
            CreateApplicationForm,
            {'jwks_uri': 'xyzs:/www.example.org'},
            'jwks_uri',
            'Enter a valid URL',
            False,
        ),
        (
            EditApplicationForm,
            {'jwks_uri': 'xyzs:/www.example.org'},
            'jwks_uri',
            'Enter a valid URL',
            False,
        ),
        # Test form with empty jwks_uri should pass.
        (
            CustomRegisterApplicationForm,
            {'jwks_uri': ''},
            'jwks_uri',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'jwks_uri': ''},
            'jwks_uri',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'jwks_uri': ''},
            'jwks_uri',
            None,
            True,
        ),
        # Test form with tos_uri valid URI.
        (
            CustomRegisterApplicationForm,
            {'tos_uri': 'https://www.example.org'},
            'tos_uri',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'tos_uri': 'https://www.example.org'},
            'tos_uri',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'tos_uri': 'https://www.example.org'},
            'tos_uri',
            None,
            True,
        ),
        # Test form with tos_uri invalid URI.
        (
            CustomRegisterApplicationForm,
            {'tos_uri': 'xyzs:/www.example.org'},
            'tos_uri',
            'Enter a valid URL',
            False,
        ),
        (
            CreateApplicationForm,
            {'tos_uri': 'xyzs:/www.example.org'},
            'tos_uri',
            'Enter a valid URL',
            False,
        ),
        (
            EditApplicationForm,
            {'tos_uri': 'xyzs:/www.example.org'},
            'tos_uri',
            'Enter a valid URL',
            False,
        ),
        # Test form with empty tos_uri should pass.
        (
            CustomRegisterApplicationForm,
            {'tos_uri': ''},
            'tos_uri',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'tos_uri': ''},
            'tos_uri',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'tos_uri': ''},
            'tos_uri',
            None,
            True,
        ),
        # Test form with policy_uri valid URI.
        (
            CustomRegisterApplicationForm,
            {'policy_uri': 'https://www.example.org'},
            'policy_uri',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'policy_uri': 'https://www.example.org'},
            'policy_uri',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'policy_uri': 'https://www.example.org'},
            'policy_uri',
            None,
            True,
        ),
        # Test form with policy_uri invalid URI.
        (
            CustomRegisterApplicationForm,
            {'policy_uri': 'xyzs:/www.example.org'},
            'policy_uri',
            'Enter a valid URL',
            False,
        ),
        (
            CreateApplicationForm,
            {'policy_uri': 'xyzs:/www.example.org'},
            'policy_uri',
            'Enter a valid URL',
            False,
        ),
        (
            EditApplicationForm,
            {'policy_uri': 'xyzs:/www.example.org'},
            'policy_uri',
            'Enter a valid URL',
            False,
        ),
        # Test form with empty policy_uri should pass.
        (
            CustomRegisterApplicationForm,
            {'policy_uri': ''},
            'policy_uri',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'policy_uri': ''},
            'policy_uri',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'policy_uri': ''},
            'policy_uri',
            None,
            True,
        ),
        # Test agree is false returns an error
        (
            CustomRegisterApplicationForm,
            {'agree': False},
            'agree',
            'You must agree to the API Terms of Service Agreement',
            False,
        ),
        # Test agree is false for other forms passes since it's automatically set to True later on
        (
            CreateApplicationForm,
            {'agree': False},
            'agree',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'agree': False},
            'agree',
            None,
            True,
        ),
        # Test not selecting require_demographic_scopes returns an error
        (
            CustomRegisterApplicationForm,
            {},
            'require_demographic_scopes',
            'Does your application need to collect beneficiary demographic information must be (Yes/No).',
            False,
        ),
        (
            CreateApplicationForm,
            {},
            'require_demographic_scopes',
            'Does your application need to collect beneficiary demographic information must be (Yes/No).',
            False,
        ),
        (
            EditApplicationForm,
            {},
            'require_demographic_scopes',
            'Does your application need to collect beneficiary demographic information must be (Yes/No).',
            False,
        ),
        # Test no description should pass
        (
            CustomRegisterApplicationForm,
            {'description': ''},
            'description',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'description': ''},
            'description',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'description': ''},
            'description',
            None,
            True,
        ),
        # Test valid description should pass
        (
            CustomRegisterApplicationForm,
            {'description': 'valid description here!'},
            'description',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'description': 'valid description here!'},
            'description',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'description': 'valid description here!'},
            'description',
            None,
            True,
        ),
        # Test valid description should pass with exactly 1,000 characters
        (
            CustomRegisterApplicationForm,
            {'description': 'T' * 1000},
            'description',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'description': 'T' * 1000},
            'description',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'description': 'T' * 1000},
            'description',
            None,
            True,
        ),
        # Test form with HTML tags in the description raises an error
        (
            CustomRegisterApplicationForm,
            {'description': '<b>Test</b> <button>Test</button> a <span>Test</span>'},
            'description',
            'The text contains HTML tags. Please use plain-text only!',
            False,
        ),
        (
            CreateApplicationForm,
            {'description': '<b>Test</b> <button>Test</button> a <span>Test</span>'},
            'description',
            'The text contains HTML tags. Please use plain-text only!',
            False,
        ),
        (
            EditApplicationForm,
            {'description': '<b>Test</b> <button>Test</button> a <span>Test</span>'},
            'description',
            'The text contains HTML tags. Please use plain-text only!',
            False,
        ),
    ],
)
def test_application_form_basic_validation(
    application_form, data, field, error_text_expected, should_pass, basic_user, create_application
):
    """Test basic validation of three forms. See comment before each one for details on specific test"""
    user = basic_user(username='john', password='123456')
    create_application('john_app', user=user)
    # Only CustomRegisterApplicationForm passes in a user
    if application_form == CustomRegisterApplicationForm:
        form = application_form(user, data)
    else:
        form = application_form(data)
    form.is_valid()
    if should_pass:
        field_errors = form.errors.as_data().get(field, [])
        assert len(field_errors) == 0
    else:
        field_errors = form.errors.as_data().get(field, [])
        assert len(field_errors) == 1
        error_text = field_errors[0].message
        assert error_text_expected in error_text


@pytest.mark.parametrize(
    'application_form, data, image_size, file_type, error_text_expected, should_pass',
    [
        # Testing valid logo_image with max dimensions
        (
            CustomRegisterApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX), int(settings.APP_LOGO_HEIGHT_MAX)),
            'jpeg',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX), int(settings.APP_LOGO_HEIGHT_MAX)),
            'jpeg',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX), int(settings.APP_LOGO_HEIGHT_MAX)),
            'jpeg',
            None,
            True,
        ),
        # Testing logo_image exceeding max width
        (
            CustomRegisterApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX) + 1, int(settings.APP_LOGO_HEIGHT_MAX)),
            'jpeg',
            'Max image width is 512.',
            False,
        ),
        (
            CreateApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX) + 1, int(settings.APP_LOGO_HEIGHT_MAX)),
            'jpeg',
            'Max image width is 512.',
            False,
        ),
        (
            EditApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX) + 1, int(settings.APP_LOGO_HEIGHT_MAX)),
            'jpeg',
            'Max image width is 512.',
            False,
        ),
        # Testing logo_image exceeding max height
        (
            CustomRegisterApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX), int(settings.APP_LOGO_HEIGHT_MAX) + 1),
            'jpeg',
            'Max image height is 512.',
            False,
        ),
        (
            CreateApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX), int(settings.APP_LOGO_HEIGHT_MAX) + 1),
            'jpeg',
            'Max image height is 512.',
            False,
        ),
        (
            EditApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX), int(settings.APP_LOGO_HEIGHT_MAX) + 1),
            'jpeg',
            'Max image height is 512.',
            False,
        ),
        # Testing png file type works
        (
            CustomRegisterApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX), int(settings.APP_LOGO_HEIGHT_MAX)),
            'png',
            None,
            True,
        ),
        (
            CreateApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX), int(settings.APP_LOGO_HEIGHT_MAX)),
            'png',
            None,
            True,
        ),
        (
            EditApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (int(settings.APP_LOGO_WIDTH_MAX), int(settings.APP_LOGO_HEIGHT_MAX)),
            'png',
            None,
            True,
        ),
        # Ensure a different file type besides jpeg, jpg, or png fails
        (
            CustomRegisterApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (50, 50),
            'bmp',
            'The file type must be JPEG, JPG, or PNG with a .jpg, .jpeg, or .png file extension!',
            False,
        ),
        (
            CreateApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (50, 50),
            'bmp',
            'The file type must be JPEG, JPG, or PNG with a .jpg, .jpeg, or .png file extension!',
            False,
        ),
        (
            EditApplicationForm,
            {'name': 'john_app', 'require_demographic_scopes': True, 'agree': True},
            (50, 50),
            'bmp',
            'The file type must be JPEG, JPG, or PNG with a .jpg, .jpeg, or .png file extension!',
            False,
        ),
    ],
)
def test_logo_image_for_all_forms(
    application_form, data, image_size, file_type, error_text_expected, should_pass, basic_user
):
    file = BytesIO()
    image = Image.new('RGB', size=image_size, color='red')
    image.save(file, file_type)
    file.seek(0)
    image = InMemoryUploadedFile(file, None, f'test.{file_type}', f'image/{file_type}', len(file.getvalue()), None)
    files = {'logo_image': image}
    # Only CustomRegisterApplicationForm passes in a user
    if application_form == CustomRegisterApplicationForm:
        user = basic_user(username='john', password='123456')
        form = application_form(user, data, files)
    else:
        form = application_form(data, files)
    form.is_valid()
    if should_pass:
        field_errors = form.errors.as_data().get('logo_image', [])
        assert len(field_errors) == 0
    else:
        field_errors = form.errors.as_data().get('logo_image', [])
        assert len(field_errors) == 1
        error_text = field_errors[0].message
        assert error_text_expected in error_text


@pytest.mark.django_db
@pytest.mark.parametrize(
    'app_form, require_demographic_scopes, use_default_non_demographic_scopes, error_text_expected, should_pass',
    [
        # Assert app_form does not give a validation error when there are no demographic scopes selected and require_demographic_scopes==False
        (
            CreateApplicationForm,
            False,
            True,
            None,
            True,
        ),
        (
            EditApplicationForm,
            False,
            True,
            None,
            True,
        ),
        # Assert there is a validation error when there are demographic scopes selected but require_demographic_scopes==False
        (
            CreateApplicationForm,
            False,
            False,
            'Cannot have demographic scopes when require_demographic_scopes==False or None.',
            False,
        ),
        (
            EditApplicationForm,
            False,
            False,
            'Cannot have demographic scopes when require_demographic_scopes==False or None.',
            False,
        ),
        # Assert that app_form gives a validation error when there are
        # no demographic scopes selected but require_demographic_scopes==True
        (
            CreateApplicationForm,
            True,
            True,
            'Must have at least one demographic scope when require_demographic_scopes==True.',
            False,
        ),
        (
            EditApplicationForm,
            True,
            True,
            'Must have at least one demographic scope when require_demographic_scopes==True.',
            False,
        ),
        # Assert that app_form is successful when there are
        # demographic scopes selected and require_demographic_scopes==True
        (
            CreateApplicationForm,
            True,
            False,
            None,
            True,
        ),
        (
            EditApplicationForm,
            True,
            False,
            None,
            True,
        ),
    ],
)
def test_demographic_scopes(
    app_form,
    require_demographic_scopes,
    use_default_non_demographic_scopes,
    should_pass,
    error_text_expected,
    basic_user,
    create_application,
):
    call_command('create_blue_button_scopes')
    default_scopes = ProtectedCapability.objects.filter(default=True)
    user = basic_user(username='john', password='123456')
    create_application('john_app', user=user)
    data = {'require_demographic_scopes': require_demographic_scopes}
    if use_default_non_demographic_scopes:
        default_non_demographic_scopes = default_scopes.exclude(slug__in=BENE_PERSONAL_INFO_SCOPES)
        data['scope'] = default_non_demographic_scopes
    else:
        data['scope'] = default_scopes
    form = app_form(data)
    form.is_valid()
    if should_pass:
        # Not sure why but the errors for demographic scopes us __all__ within form.errors
        field_errors = form.errors.as_data().get('__all__', [])
        assert len(field_errors) == 0
    else:
        # Not sure why but the errors for demographic scopes us __all__ within form.errors
        field_errors = form.errors.as_data().get('__all__', [])
        assert len(field_errors) == 1
        error_text = field_errors[0].message
        assert error_text_expected in error_text


@pytest.mark.django_db
@pytest.mark.parametrize(
    'data, should_add_user_to_data, error_text_expected, should_pass',
    [
        # Ensure trying to create a new user selection fails validation if you've selected an existing user
        (
            {'user_mode': 'new'},
            True,
            'You cannot select a user when choosing the "Create New User" option.',
            False,
        ),
        # Ensure trying to create a new user selection passes validation with no existing user selected
        (
            {'user_mode': 'new'},
            False,
            None,
            True,
        ),
        # Ensure selecting the 'existing user' user_mode fails validation if you don't select a user on the form
        (
            {'user_mode': 'existing'},
            False,
            'You must select an existing user when choosing the "Choose Existing User" option.',
            False,
        ),
        # Ensure selecting the 'existing user' user_mode passes validation if you select a user on the form
        (
            {'user_mode': 'existing'},
            True,
            None,
            True,
        ),
    ],
)
def test_create_application_form_user_mode_selection(
    data, should_add_user_to_data, error_text_expected, should_pass, basic_user, create_application
):
    user = basic_user(username='john', password='123456')
    create_application('john_app', user=user)
    if should_add_user_to_data:
        data['user'] = user

    form = CreateApplicationForm(data)
    form.is_valid()
    if should_pass:
        field_errors = form.errors.as_data().get('user', [])
        assert len(field_errors) == 0
    else:
        field_errors = form.errors.as_data().get('user', [])
        assert len(field_errors) == 1
        error_text = field_errors[0].message
        assert error_text_expected in error_text


@pytest.mark.django_db
@pytest.mark.parametrize(
    'app_form, data, include_scopes, include_user',
    [
        # Ensure each from passes with minimum required fields
        (
            # Just requires name, require_demographic_scopes, and agree
            CustomRegisterApplicationForm,
            {
                'name': 'john_app_new',
                'client_type': '',
                'authorization_grant_type': '',
                'redirect_uris': '',
                'logo_uri': '',
                'logo_image': '',
                'website_uri': '',
                'description': '',
                'policy_uri': '',
                'tos_uri': '',
                'support_email': '',
                'support_phone_number': '',
                'contacts': '',
                'require_demographic_scopes': True,
                'agree': True,
            },
            False,
            False,
        ),
        (
            # requires name, require_demographic_scopes, user_mode, organization_name, allowed_auth_type, and scope
            CreateApplicationForm,
            {
                'name': 'john_new_app',
                'user_mode': 'new',
                'user': None,
                'organization_name': "I'm an org name",
                'contacts': '',
                'agree': '',
                'redirect_uris': '',
                'require_demographic_scopes': True,
                # Scope gets set later in function
                'scope': '',
                'policy_uri': '',
                'tos_uri': '',
                'website_uri': '',
                'support_email': '',
                'support_phone_number': '',
                'logo_image': '',
                'description': '',
                'internal_application_labels': '',
                'jwks_uri': '',
                'allowed_auth_type': 'AUTH_CODE',
                'part_d_eob_only': '',
            },
            True,
            False,
        ),
        (
            # requires data_access_type, client_id, user, client_type,
            # authorization_grant_type, name, require_demographic_scopes,
            # user_mode, organization_name, allowed_auth_type, redirect_uri's, and scope
            EditApplicationForm,
            {
                'data_access_type': 'THIRTEEN_MONTH',
                'client_id': 'test-client-id',
                # User gets set inside test function
                'user': None,
                'client_type': 'confidential',
                # User mode automatically gets set to existing when instantiated
                'user_mode': None,
                'authorization_grant_type': 'authorization-code',
                'client_secret_plain': '',
                'client_secret': '',
                'name': 'john_new_app',
                'skip_authorization': '',
                # Scope set in testing function
                'scope': '',
                'require_demographic_scopes': True,
                'agree': '',
                'allowed_auth_type': 'AUTH_CODE',
                'op_tos_uri': '',
                'op_policy_uri': '',
                'client_uri': '',
                'website_uri': '',
                'redirect_uris': 'http://localhost:8000/callback',
                'logo_uri': '',
                'logo_image': '',
                'tos_uri': '',
                'policy_uri': '',
                'software_id': '',
                'contacts': '',
                'support_email': '',
                'support_phone_number': '',
                'description': '',
                'internal_application_labels': '',
                'active': '',
                'first_active': '',
                'last_active': '',
                'jwks_uri': '',
                'part_d_eob_only': '',
            },
            True,
            True,
        ),
    ],
)
def test_minimum_required_fields_for_all_forms(
    app_form, data, include_scopes, include_user, basic_user, create_application
):
    user = basic_user(username='john', password='123456')
    create_application('john_app', user=user)
    if include_scopes:
        call_command('create_blue_button_scopes')
        default_scopes = ProtectedCapability.objects.filter(default=True)
        data['scope'] = default_scopes
    if include_user:
        data['user'] = user
    # Only CustomRegisterApplicationForm passes in a user
    if app_form == CustomRegisterApplicationForm:
        form = app_form(user, data)
    else:
        form = app_form(data)
    form.is_valid()
    assert form.errors == {}
