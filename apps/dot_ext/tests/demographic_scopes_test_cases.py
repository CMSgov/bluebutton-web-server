"""
    Test Cases for demographic scopes related testing

    Dictionaries included:

        FORM_OAUTH2_SCOPES_TEST_CASES - For testing OAUTH2 form cleaned data

        VIEW_OAUTH2_SCOPES_TEST_CASES - For testing OAUTH2 authorization views
"""
# Scopes lists for testing
APPLICATION_SCOPES_FULL = ['patient/Patient.read', 'profile',
                           'patient/ExplanationOfBenefit.read', 'patient/Coverage.read',
                           'capability-a', 'capability-b']
APPLICATION_SCOPES_NON_DEMOGRAPHIC = ['patient/ExplanationOfBenefit.read',
                                      'patient/Coverage.read', 'capability-a', 'capability-b']

# Various scopes used to test requested and assigned/granted to access tokens
SCOPES_JUST_PATIENT = ['patient/Patient.read']
SCOPES_JUST_PATIENT_AND_A = ['patient/Patient.read', 'capability-a']
SCOPES_JUST_A = ['capability-a']
SCOPES_JUST_EOB_AND_B = ['patient/ExplanationOfBenefit.read', 'capability-b']
SCOPES_JUST_EMPTY = []

# Scope to base URL PATH mapping.
SCOPES_TO_URL_BASE_PATH = {
    "profile": {
        "base_path": "/v1/connect/userinfo",
        "is_fhir_url": False,
    },
    "patient/Patient.read": {
        "base_path": "/v1/fhir/Patient",
        "is_fhir_url": True,
        # The ReadView should be tested.
        "test_readview": True,
    },
    "patient/ExplanationOfBenefit.read": {
        "base_path": "/v1/fhir/ExplanationOfBenefit",
        "is_fhir_url": True,
    },
    "patient/Coverage.read": {
        "base_path": "/v1/fhir/Coverage",
        "is_fhir_url": True,
    },
}

"""
    FORM_OAUTH2_SCOPES_TEST_CASES test case dictionary
    --------------------------------------------------

    USED in the following test:
      apps.dot_ext.tests.test_form_oauth2
                        .TestSimpleAllowFormForm.test_form()

    Test case dictionary key and value meanings:

    REQUEST PARAMETERS:
      These are used to setup the authorization request.

      - request_bene_block_personal_choice = [None, True, False]
            Did the beneficiary choose to block demographic info?
      - request_scopes = The scopes being requested in the authorization request.

    EXPECTED RESULTS:
      These are used to validate the authorization request results.

      - result_form_is_valid = [True, False]
            What is the expected result for form.is_valid()?
      - result_token_scopes_granted = The List of scopes expected
            to be assigned to the resulting access token.
"""
FORM_OAUTH2_SCOPES_TEST_CASES = {
    "test 1: block_personal_choice = None": {
        # Request:
        "request_bene_block_personal_choice": None,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_form_is_valid": True,
        "result_token_scopes_granted": APPLICATION_SCOPES_FULL,
    },
    "test 2: block_personal_choice = True": {
        # Request:
        "request_bene_block_personal_choice": True,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_form_is_valid": True,
        "result_token_scopes_granted": APPLICATION_SCOPES_NON_DEMOGRAPHIC,
    },
    "test 3: block_personal_choice = False": {
        # Request:
        "request_bene_block_personal_choice": False,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_form_is_valid": True,
        "result_token_scopes_granted": APPLICATION_SCOPES_FULL,
    },
    "test 4: block = False request just EOB and B": {
        # Request:
        "request_bene_block_personal_choice": False,
        "request_scopes": SCOPES_JUST_EOB_AND_B,
        # Result:
        "result_form_is_valid": True,
        "result_token_scopes_granted": SCOPES_JUST_EOB_AND_B,
    },
    "test 5: block = False request just PATIENT and A": {
        # Request:
        "request_bene_block_personal_choice": False,
        "request_scopes": SCOPES_JUST_PATIENT_AND_A,
        # Result:
        "result_form_is_valid": True,
        "result_token_scopes_granted": SCOPES_JUST_PATIENT_AND_A,
    },
    "test 6: block = True request just EOB and B": {
        # Request:
        "request_bene_block_personal_choice": True,
        "request_scopes": SCOPES_JUST_EOB_AND_B,
        # Result:
        "result_form_is_valid": True,
        "result_token_scopes_granted": SCOPES_JUST_EOB_AND_B,
    },
    "test 7: block = True request just PATIENT and A": {
        # Request:
        "request_bene_block_personal_choice": True,
        "request_scopes": SCOPES_JUST_PATIENT_AND_A,
        # Result:
        "result_form_is_valid": True,
        "result_token_scopes_granted": SCOPES_JUST_A,
    },
    "test 8: block = False request just PATIENT": {
        # Request:
        "request_bene_block_personal_choice": False,
        "request_scopes": SCOPES_JUST_PATIENT,
        # Result:
        "result_form_is_valid": True,
        "result_token_scopes_granted": SCOPES_JUST_PATIENT,
    },
    "test 9: block = True request just PATIENT": {
        # Request:
        "request_bene_block_personal_choice": True,
        "request_scopes": SCOPES_JUST_PATIENT,
        # Result:
        "result_form_is_valid": True,
        "result_token_scopes_granted": SCOPES_JUST_EMPTY,
    },
    "test 10: block = False request just EMPTY": {
        # Request:
        "request_bene_block_personal_choice": False,
        "request_scopes": SCOPES_JUST_EMPTY,
        # Result:
        "result_form_is_valid": False,
        "result_token_scopes_granted": SCOPES_JUST_EMPTY,
    },
}

"""
    VIEW_OAUTH2_SCOPES_TEST_CASES test case dictionary
    --------------------------------------------------

    USED in the following test:
      apps.dot_ext.tests.test_views
                        .TestAuthorizationView.test_post_with_request_block_personal_choice()

    Test case dictionary key and value meanings:

    REQUEST PARAMETERS:
      These are used to setup the authorization request.

      - request_bene_block_personal_choice = [None, True, False]
            Does the beneficiary choose to block demographic info?
      - request_app_requires_demographic = [None, True, False]
            Does the application choose to require demographic info?
      - request_scopes = The scopes being requested in the authorization request.

    EXPECTED RESULTS:
      These are used to validate the authorization request results.

      - result_has_error = [True, False]
            Is an error in the result expected?
      - result_token_scopes_granted = The List of scopes expected
            to be assigned to the resulting access token.
      - result_raises_exception = The exception raised.
      - result_exception_mesg =  Exception message REGEX.
"""
VIEW_OAUTH2_SCOPES_TEST_CASES = {
    # Tests for app_require_demographic_scopes = None
    "test 1: app_requires = None bene_block = None": {
        # Request:
        "request_app_requires_demographic": None,
        "request_bene_block_personal_choice": None,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": APPLICATION_SCOPES_FULL,
    },
    "test 2: app_requires = None bene_block = True": {
        # Request:
        "request_app_requires_demographic": None,
        "request_bene_block_personal_choice": True,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": APPLICATION_SCOPES_NON_DEMOGRAPHIC,
    },
    "test 3: app_requires = None bene_block = False": {
        # Request:
        "request_app_requires_demographic": None,
        "request_bene_block_personal_choice": False,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": APPLICATION_SCOPES_FULL,
    },
    # Tests for request_app_requires_demographic = True
    "test 4: app_requires = True bene_block = None": {
        # Request:
        "request_app_requires_demographic": True,
        "request_bene_block_personal_choice": None,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": APPLICATION_SCOPES_FULL,
    },
    "test 5: app_requires = True bene_block = True": {
        # Request:
        "request_app_requires_demographic": True,
        "request_bene_block_personal_choice": True,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": APPLICATION_SCOPES_NON_DEMOGRAPHIC,
    },
    "test 6: app_requires = True bene_block = False": {
        # Request:
        "request_app_requires_demographic": True,
        "request_bene_block_personal_choice": False,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": APPLICATION_SCOPES_FULL,
    },
    # Tests for request_app_requires_demographic = False
    "test 7: app_requires = False bene_block = None": {
        # Request:
        "request_app_requires_demographic": False,
        "request_bene_block_personal_choice": None,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": APPLICATION_SCOPES_NON_DEMOGRAPHIC,
    },
    "test 8: app_requires = False bene_block = True": {
        # Request:
        "request_app_requires_demographic": False,
        "request_bene_block_personal_choice": True,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": APPLICATION_SCOPES_NON_DEMOGRAPHIC,
    },
    "test 9: app_requires = False bene_block = False": {
        # Request:
        "request_app_requires_demographic": False,
        "request_bene_block_personal_choice": False,
        "request_scopes": APPLICATION_SCOPES_FULL,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": APPLICATION_SCOPES_NON_DEMOGRAPHIC,
    },
    # Misc tests where only partial scopes are requested for authorization
    "test 10: app_requires = True bene_block = False request just EOB and B": {
        # Request:
        "request_app_requires_demographic": True,
        "request_bene_block_personal_choice": False,
        "request_scopes": SCOPES_JUST_EOB_AND_B,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": SCOPES_JUST_EOB_AND_B,
    },
    "test 11: app_requires = None bene_block = None request just PATIENT and A": {
        # Request:
        "request_app_requires_demographic": None,
        "request_bene_block_personal_choice": None,
        "request_scopes": SCOPES_JUST_PATIENT_AND_A,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": SCOPES_JUST_PATIENT_AND_A,
    },
    "test 12: app_requires = True bene_block = False request just PATIENT and A": {
        # Request:
        "request_app_requires_demographic": True,
        "request_bene_block_personal_choice": False,
        "request_scopes": SCOPES_JUST_PATIENT_AND_A,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": SCOPES_JUST_PATIENT_AND_A,
    },
    "test 13: app_requires = False bene_block = False request just PATIENT and A": {
        # Request:
        "request_app_requires_demographic": False,
        "request_bene_block_personal_choice": False,
        "request_scopes": SCOPES_JUST_PATIENT_AND_A,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": SCOPES_JUST_A,
    },
    "test 14: app_requires = True bene_block = True request just PATIENT and A": {
        # Request:
        "request_app_requires_demographic": True,
        "request_bene_block_personal_choice": True,
        "request_scopes": SCOPES_JUST_PATIENT_AND_A,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": SCOPES_JUST_A,
    },
    "test 15: app_requires = None bene_block = True request just PATIENT and A": {
        # Request:
        "request_app_requires_demographic": None,
        "request_bene_block_personal_choice": True,
        "request_scopes": SCOPES_JUST_PATIENT_AND_A,
        # Result:
        "result_has_error": False,
        "result_token_scopes_granted": SCOPES_JUST_A,
    },
    # Testing initial auth request has request_scopes = None
    #   The POST to oauth2_provider:authorize must have scope in the payload.
    "test 16: app_requires = True bene_block = False request scopes = None": {
        # Request:
        "request_app_requires_demographic": True,
        "request_bene_block_personal_choice": False,
        "request_scopes": None,
        # Result:  NOTE: This case has empty scopes on POST!
        "result_has_error": True,
        "result_raises_exception": AssertionError,
    },
    # Testing case that produce ValueError exception
    "test 17: app_requires = False bene_block = False request just PATIENT error=True": {
        # Request:
        "request_app_requires_demographic": False,
        "request_bene_block_personal_choice": False,
        "request_scopes": SCOPES_JUST_PATIENT,
        # Result:  NOTE: Since Patient is not allowed,
        #                this case results in having empty scopes on post auth!
        "result_has_error": True,
        "result_raises_exception": ValueError,
        "result_exception_mesg": "Scopes must be set on post auth.",
    },
    # Testing cases that produces AssertionError in _authorize_and_request_token()
    "test 18: app_requires = True bene_block = False request just empty scopes error=True": {
        # Request:
        "request_app_requires_demographic": True,
        "request_bene_block_personal_choice": False,
        "request_scopes": SCOPES_JUST_EMPTY,
        # Result:  NOTE: This case has an empty List in POST request payload!
        "result_has_error": True,
        "result_raises_exception": AssertionError,
        "result_exception_mesg": "200 != 302",
    },
}
