from apps.dot_ext.forms import SimpleAllowForm
from apps.dot_ext.scopes import CapabilitiesScopes
from apps.test import BaseApiTest
from django.conf import settings


class TestSimpleAllowFormForm(BaseApiTest):
    fixtures = ['scopes.json']

    def test_form(self):
        """
            Test form related to scopes and BENE block_personal_choice.
        """
        full_scopes_list = CapabilitiesScopes().get_default_scopes()
        non_personal_scopes_list = list(set(full_scopes_list) - set(settings.BENE_PERSONAL_INFO_SCOPES))

        data = {'redirect_uri': 'http://localhost:3000/bluebutton/callback/',
                'scope': ' '.join(full_scopes_list),
                'client_id': 'AAAAAAAAAA1111111111111111AAAAAAAAAAAAAA',
                'state': 'ba0a6e3c704ced52c7788331e6bab262',
                'response_type': 'code',
                'code_challenge': '',
                'code_challenge_method': '',
                'allow': 'Allow'}

        # 1. Test with block_personal_choice = False
        #        Should have full scopes list.
        data['block_personal_choice'] = 'False'
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(full_scopes_list),
                         sorted(cleaned_data['scope'].split()))

        # 2. Test with block_personal_choice = True
        #        Should have non personal scopes list.
        data['block_personal_choice'] = 'True'
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data
        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(non_personal_scopes_list),
                         sorted(cleaned_data['scope'].split()))
