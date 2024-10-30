from apps.dot_ext.forms import SimpleAllowForm
from apps.test import BaseApiTest
from ..models import Application
from .demographic_scopes_test_cases import FORM_OAUTH2_SCOPES_TEST_CASES


class TestSimpleAllowFormForm(BaseApiTest):
    fixtures = ['scopes.json']

    def test_form(self):
        """
        Test FORM related to beneficiary "share_demographic_scopes" values.

        The "FORM_OAUTH2_SCOPES_TEST_CASES" dictionary of test cases
        for the different values is used.
        """
        # Create a test application with require_demographic_scopes = None
        redirect_uri = 'com.custom.bluebutton://example.it'

        # Give the app some additional scopes.
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])

        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        # Loop through test cases in dictionary.
        cases = FORM_OAUTH2_SCOPES_TEST_CASES
        for case in cases:
            # Setup request parameters for test case.
            request_bene_share_demographic_scopes = cases[case]["request_bene_share_demographic_scopes"]
            request_scopes = cases[case]["request_scopes"]

            # Setup expected results for test case.
            result_form_is_valid = cases[case]["result_form_is_valid"]
            result_token_scopes_granted = cases[case]["result_token_scopes_granted"]

            data = {'redirect_uri': redirect_uri,
                    'client_id': 'AAAAAAAAAA1111111111111111AAAAAAAAAAAAAA',
                    'state': 'ba0a6e3c704ced52c7788331e6bab262',
                    'response_type': 'code',
                    'code_challenge': '',
                    'code_challenge_method': '',
                    'allow': 'Allow'}

            # Scopes requested in the form.
            data['scope'] = ' '.join(request_scopes)

            # Does the beneficiary share demographic info in the form?
            if cases[case]["request_bene_share_demographic_scopes"] is not None:
                data['share_demographic_scopes'] = request_bene_share_demographic_scopes

            form = SimpleAllowForm(data)

            # Is the form valid?
            if result_form_is_valid:
                self.assertTrue(form.is_valid())
            else:
                self.assertFalse(form.is_valid())
                # Continue to next test case
                continue

            cleaned_data = form.cleaned_data

            self.assertNotEqual(cleaned_data['scope'].split(), None)

            # Test for expected scopes in cleand form data
            self.assertEqual(sorted(result_token_scopes_granted),
                             sorted(cleaned_data['scope'].split()))
