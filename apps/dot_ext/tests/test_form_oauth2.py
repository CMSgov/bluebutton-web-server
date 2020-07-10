from apps.dot_ext.forms import SimpleAllowForm
from apps.dot_ext.scopes import CapabilitiesScopes
from apps.test import BaseApiTest
from django.conf import settings
from ..models import Application



class TestSimpleAllowFormForm(BaseApiTest):
    fixtures = ['scopes.json']

    def test_form(self):
        """
            Test form related to scopes and BENE block_personal_choice.
        """
        # Create a test application with require_demographic_scopes = None
        redirect_uri = 'com.custom.bluebutton://example.it'
        # create a user
        self._create_user('app_user', '123456')
        # Give the app some additional scopes.
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        data = {'redirect_uri': 'http://localhost:3000/bluebutton/callback/',
                'client_id': 'AAAAAAAAAA1111111111111111AAAAAAAAAAAAAA',
                'state': 'ba0a6e3c704ced52c7788331e6bab262',
                'response_type': 'code',
                'code_challenge': '',
                'code_challenge_method': '',
                'allow': 'Allow'}

        """ 
            1. TEST:   block_personal_choice = False
                       application.require_demographic_scopes = None

               RESULT: Should have full scopes list.
        """ 
        # Get default scopes available to application.
        application.require_demographic_scopes = None
        app_default_scopes_list = CapabilitiesScopes().get_default_scopes(application=application)
        non_personal_scopes_list = list(set(app_default_scopes_list) - set(settings.BENE_PERSONAL_INFO_SCOPES))
        data['scope'] = ' '.join(app_default_scopes_list)

        data['block_personal_choice'] = 'False'
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(app_default_scopes_list),
                         sorted(cleaned_data['scope'].split()))

        """ 
            2. TEST:   block_personal_choice = True 
                       application.require_demographic_scopes = None

               RESULT: Should have non personal scopes list.
        """
        # Get default scopes available to application.
        application.require_demographic_scopes = None
        app_default_scopes_list = CapabilitiesScopes().get_default_scopes(application=application)
        non_personal_scopes_list = list(set(app_default_scopes_list) - set(settings.BENE_PERSONAL_INFO_SCOPES))
        data['scope'] = ' '.join(app_default_scopes_list)

        data['block_personal_choice'] = 'True'
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(non_personal_scopes_list),
                         sorted(cleaned_data['scope'].split()))

        """ 
            3. TEST:   block_personal_choice = False
                       application.require_demographic_scopes = True

               RESULT: Should have full scopes list.
        """ 
        # Get default scopes available to application.
        application.require_demographic_scopes = True
        app_default_scopes_list = CapabilitiesScopes().get_default_scopes(application=application)
        non_personal_scopes_list = list(set(app_default_scopes_list) - set(settings.BENE_PERSONAL_INFO_SCOPES))
        data['scope'] = ' '.join(app_default_scopes_list)

        data['block_personal_choice'] = 'False'
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(app_default_scopes_list),
                         sorted(cleaned_data['scope'].split()))

        """ 
            4. TEST:   block_personal_choice = True 
                       application.require_demographic_scopes = True

               RESULT: Should have non personal scopes list.
        """
        # Get default scopes available to application.
        application.require_demographic_scopes = True
        app_default_scopes_list = CapabilitiesScopes().get_default_scopes(application=application)
        non_personal_scopes_list = list(set(app_default_scopes_list) - set(settings.BENE_PERSONAL_INFO_SCOPES))
        data['scope'] = ' '.join(app_default_scopes_list)

        data['block_personal_choice'] = 'True'
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(non_personal_scopes_list),
                         sorted(cleaned_data['scope'].split()))

        """ 
            5. TEST:   block_personal_choice = False
                       application.require_demographic_scopes = False

               RESULT: Should have full scopes list.
        """ 
        # Get default scopes available to application.
        application.require_demographic_scopes = False
        app_default_scopes_list = CapabilitiesScopes().get_default_scopes(application=application)
        non_personal_scopes_list = list(set(app_default_scopes_list) - set(settings.BENE_PERSONAL_INFO_SCOPES))
        data['scope'] = ' '.join(app_default_scopes_list)

        data['block_personal_choice'] = 'False'
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(app_default_scopes_list),
                         sorted(cleaned_data['scope'].split()))

        """ 
            6. TEST:   block_personal_choice = True 
                       application.require_demographic_scopes = False

               RESULT: Should have non personal scopes list.
        """
        # Get default scopes available to application.
        application.require_demographic_scopes = False
        app_default_scopes_list = CapabilitiesScopes().get_default_scopes(application=application)
        non_personal_scopes_list = list(set(app_default_scopes_list) - set(settings.BENE_PERSONAL_INFO_SCOPES))
        data['scope'] = ' '.join(app_default_scopes_list)

        data['block_personal_choice'] = 'True'
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(non_personal_scopes_list),
                         sorted(cleaned_data['scope'].split()))
