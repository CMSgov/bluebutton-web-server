from django.conf import settings

ERR_CCM_S256_REQUIRED = "PKCE code_challenge_method required to be S256"
ERR_CC_REQUIRED = "PKCE code_challenge required"
ERR_CCM_REQUIRED = "code_challenge_method required for pkce, missing parameter: code_challenge_method=S256"

GRANT_MODEL = getattr(settings, "OAUTH2_PROVIDER_GRANT_MODEL", "oauth2_provider.Grant")

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
