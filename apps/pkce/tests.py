from django.test import TestCase
from oauthlib.common import Request
from oauthlib.oauth2.rfc6749.errors import InvalidRequestError

from apps.pkce.oauth2_server import validate_code_challenge_method, validate_redirect_uri_pkce
from apps.pkce.oauth2_server import ERR_CCM_REQUIRED, ERR_CC_REQUIRED, ERR_CCM_S256_REQUIRED

PKCE_URIS = {
    "MISSING_CODE_CHALLENGE_METHOD_PARAM": ("/v2/o/authorize/b787ff17-e865-4893-aa79-4016ae5677a0/?"
                                            "response_type=code&client_id=XQFC5iseB84YGOidlqy0L9blhauz0pIffPnMi0qJ&"
                                            "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Ftestclient%2Fcallback&"
                                            "state=QCh2XTdgS3RdfEI1Qz0uOll8KStOdShwfVlzWyNBTGA%3D&"
                                            "code_challenge=9GLy9RNcZrhuqk-kSSbqOHkkKTV8Og8PIbtkMPA7XjA%3D"),
    "CODE_CHALLENGE_METHOD_NOT_S256": ("/v2/o/authorize/b787ff17-e865-4893-aa79-4016ae5677a0/?"
                                       "response_type=code&client_id=XQFC5iseB84YGOidlqy0L9blhauz0pIffPnMi0qJ&"
                                       "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Ftestclient%2Fcallback&"
                                       "state=QCh2XTdgS3RdfEI1Qz0uOll8KStOdShwfVlzWyNBTGA%3D&"
                                       "code_challenge=9GLy9RNcZrhuqk-kSSbqOHkkKTV8Og8PIbtkMPA7XjA%3D&"
                                       "code_challenge_method=plain"),
    "MISSING_CODE_CHALLENGE_PARAM": ("/v2/o/authorize/b787ff17-e865-4893-aa79-4016ae5677a0/?"
                                     "response_type=code&client_id=XQFC5iseB84YGOidlqy0L9blhauz0pIffPnMi0qJ&"
                                     "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Ftestclient%2Fcallback&"
                                     "state=QCh2XTdgS3RdfEI1Qz0uOll8KStOdShwfVlzWyNBTGA%3D&code_challenge_method=S256"),
    "MISSING_CODE_CHALLENGE_VAL": ("/v2/o/authorize/b787ff17-e865-4893-aa79-4016ae5677a0/?"
                                   "response_type=code&client_id=XQFC5iseB84YGOidlqy0L9blhauz0pIffPnMi0qJ&"
                                   "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Ftestclient%2Fcallback&"
                                   "state=QCh2XTdgS3RdfEI1Qz0uOll8KStOdShwfVlzWyNBTGA%3D&code_challenge=&"
                                   "code_challenge_method=S256"),
    "AUTH_URI_W_S256_AND_CHALLENGE_CODE": ("/v2/o/authorize/b787ff17-e865-4893-aa79-4016ae5677a0/?"
                                           "response_type=code&client_id=XQFC5iseB84YGOidlqy0L9blhauz0pIffPnMi0qJ&"
                                           "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Ftestclient%2Fcallback&"
                                           "state=QCh2XTdgS3RdfEI1Qz0uOll8KStOdShwfVlzWyNBTGA%3D&"
                                           "code_challenge=9GLy9RNcZrhuqk-kSSbqOHkkKTV8Og8PIbtkMPA7XjA%3D&"
                                           "code_challenge_method=S256"),
    "AUTH_URI_NO_PKCE_PARAMS": ("/v2/o/authorize/b787ff17-e865-4893-aa79-4016ae5677a0/?"
                                "response_type=code&client_id=XQFC5iseB84YGOidlqy0L9blhauz0pIffPnMi0qJ&"
                                "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Ftestclient%2Fcallback&"
                                "state=QCh2XTdgS3RdfEI1Qz0uOll8KStOdShwfVlzWyNBTGA%3D"), }


class TestOAuth2PKCEValidation(TestCase):
    def test_redirect_validation(self):
        r = validate_redirect_uri_pkce(Request(uri=PKCE_URIS['AUTH_URI_W_S256_AND_CHALLENGE_CODE']))
        self.assertFalse(r)

    def test_non_pkce_validation(self):
        r = validate_code_challenge_method(Request(uri=PKCE_URIS['AUTH_URI_NO_PKCE_PARAMS']))
        self.assertFalse(r)

    def test_pkce_validation(self):
        r = validate_code_challenge_method(Request(uri=PKCE_URIS["AUTH_URI_W_S256_AND_CHALLENGE_CODE"]))
        self.assertFalse(r)

    def test_pkce_validation_no_ccm(self):
        with self.assertRaisesMessage(InvalidRequestError, ERR_CCM_REQUIRED):
            validate_code_challenge_method(Request(uri=PKCE_URIS["MISSING_CODE_CHALLENGE_METHOD_PARAM"]))

    def test_pkce_validation_ccm_not_s256(self):
        with self.assertRaisesMessage(InvalidRequestError, ERR_CCM_S256_REQUIRED):
            validate_code_challenge_method(Request(uri=PKCE_URIS["CODE_CHALLENGE_METHOD_NOT_S256"]))

    def test_pkce_validation_no_cc(self):
        with self.assertRaisesMessage(InvalidRequestError, ERR_CC_REQUIRED):
            validate_code_challenge_method(Request(uri=PKCE_URIS["MISSING_CODE_CHALLENGE_PARAM"]))

    def test_pkce_validation_cc_no_val(self):
        with self.assertRaisesMessage(InvalidRequestError, ERR_CC_REQUIRED):
            validate_code_challenge_method(Request(uri=PKCE_URIS["MISSING_CODE_CHALLENGE_VAL"]))
