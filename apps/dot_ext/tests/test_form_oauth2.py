from waffle.testutils import override_switch
from apps.test import BaseApiTest
from apps.dot_ext.forms import SimpleAllowForm


class TestSimpleAllowFormForm(BaseApiTest):

    @override_switch('require-scopes', active=True)
    def assertFormValidWithRequireScopes(self, data):
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        return form.cleaned_data

    def assertFormValid(self, data):
        form = SimpleAllowForm(data)
        self.assertTrue(form.is_valid())
        return form.cleaned_data

    def test_form(self):
        """
            Test form related to scopes and require-scopes feature switch.
        """
        full_scopes_list = 'patient/Patient.read profile patient/ExplanationOfBenefit.read patient/Coverage.read'
        non_personal_scopes_list = 'patient/ExplanationOfBenefit.read patient/Coverage.read'

        data = {'redirect_uri': 'http://localhost:3000/bluebutton/callback/',
                'scope': full_scopes_list,
                'client_id': 'AAAAAAAAAA1111111111111111AAAAAAAAAAAAAA',
                'state': 'ba0a6e3c704ced52c7788331e6bab262',
                'response_type': 'code',
                'code_challenge': '',
                'code_challenge_method': '',
                'allow': 'Allow'}

        # Test with block_personal_choice = False
        data['block_personal_choice'] = 'False'
        #     1. with require-scopes switch disabled.
        #        Should have full scopes list.
        cleaned_data = self.assertFormValid(data)
        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(full_scopes_list.split()),
                         sorted(cleaned_data['scope'].split()))
        #     2. with require-scopes switch enabled.
        #        Should have full scopes list.
        cleaned_data = self.assertFormValidWithRequireScopes(data)
        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(full_scopes_list.split()),
                         sorted(cleaned_data['scope'].split()))

        # Test with block_personal_choice = True
        data['block_personal_choice'] = 'True'
        #     1. with require-scopes switch disabled.
        #        Should have non personal scopes list.
        cleaned_data = self.assertFormValid(data)
        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(non_personal_scopes_list.split()),
                         sorted(cleaned_data['scope'].split()))
        #     2. with require-scopes switch enabled.
        #        Should have non personal scopes list.
        cleaned_data = self.assertFormValidWithRequireScopes(data)
        self.assertNotEqual(cleaned_data['scope'].split(), None)
        self.assertEqual(sorted(non_personal_scopes_list.split()),
                         sorted(cleaned_data['scope'].split()))
