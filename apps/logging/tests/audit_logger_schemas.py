'''
  Log entry schemas used for tests in apps/logging/tests/test_audit_loggers.py
  See the following for information about the JSON Schema vocabulary: https://json-schema.org/
'''
ACCESS_TOKEN_AUTHORIZED_LOG_SCHEMA = {
    "title": "AccessTokenAuthorizedLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "AccessToken"},
        "action": {"pattern": "authorized"},
        "auth_grant_type": {"pattern": "password"},
        "id": {"type": "integer"},
        "scopes": {"pattern": "read write patient"},
        "user": {"type": "object",
                 "properties": {
                     "id": {"type": "integer"},
                     "username": {"pattern": "John"}}},
        "crosswalk": {"type": "object",
                      "properties": {
                          "id": {"type": "integer"},
                          "user_hicn_hash": {"pattern": "96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7"},
                          "user_mbi_hash": {"pattern": "98765432137efea543f4f370f96f1dbf01c3e3129041dba3ea43675987654321"},
                          "fhir_id": {"pattern": "-20140000008325"},
                          "user_id_type": {"pattern": "H"}}},
    },
    "required": ["type", "action", "auth_grant_type", "id", "scopes", "user", "crosswalk"]
}

AUTHENTICATION_START_LOG_SCHEMA = {
    "title": "AuthenticationStartLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "Authentication:start"},
        "sls_status": {"pattern": "OK"},
        "sub": {"pattern": "00112233-4455-6677-8899-aabbccddeeff"},
        "sls_mbi_format_valid": {"type": "boolean"},
        "sls_mbi_format_msg": {"pattern": "Valid"},
        "sls_mbi_format_synthetic": {"type": "boolean"},
        "sls_hicn_hash": {"pattern": "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948"},
        "sls_mbi_hash": {"pattern": "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28"},
    },
    "required": ["type", "sls_status", "sub", "sls_mbi_format_valid", "sls_mbi_format_msg",
                 "sls_mbi_format_synthetic", "sls_hicn_hash", "sls_mbi_hash"]
}

AUTHENTICATION_SUCCESS_LOG_SCHEMA = {
    "title": "AuthenticationSuccessLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "Authentication:success"},
        "sub": {"pattern": "00112233-4455-6677-8899-aabbccddeeff"},
        "user": {"type": "object",
                 "properties": {
                     "id": {"type": "integer"},
                     "username": {"pattern": "00112233-4455-6677-8899-aabbccddeeff"},
                     "crosswalk": {
                         "type": "object",
                         "properties": {
                             "id": {"type": "integer"},
                             "user_hicn_hash": {"pattern": "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948"},
                             "user_mbi_hash": {"pattern": "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28"},
                             "fhir_id": {"pattern": "-20140000008325"},
                             "user_id_type": {"pattern": "M"}}}}},
        "auth_crosswalk_action": {"pattern": "C"},
    },
    "required": ["type", "sub", "user", "auth_crosswalk_action"]
}

AUTHORIZATION_LOG_SCHEMA = {
    "title": "AuthorizationLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "Authorization"},
        "auth_status": {"pattern": "OK"},
        "auth_status_code": {"type": "null"},
        "user": {"type": "object",
                 "properties": {
                     "id": {"type": "integer"},
                     "username": {"pattern": "anna"},
                     "crosswalk": {
                         "type": "object",
                         "properties": {
                             "id": {"type": "integer"},
                             "user_hicn_hash": {"pattern": "96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7"},
                             "user_mbi_hash": {"pattern": "98765432137efea543f4f370f96f1dbf01c3e3129041dba3ea43675987654321"},
                             "fhir_id": {"pattern": "-20140000008325"},
                             "user_id_type": {"pattern": "H"}}}}},
        "application": {"type": "object",
                        "properties": {
                            "id": {"pattern": "1"},
                            "name": {"pattern": "an app"}}},
        "share_demographic_scopes": {"pattern": "^$"},
        "scopes": {"pattern": "capability-a"},
        "allow": {"type": "boolean"},
        "access_token_delete_cnt": {"type": "integer", "enum": [0]},
        "refresh_token_delete_cnt": {"type": "integer", "enum": [0]},
        "data_access_grant_delete_cnt": {"type": "integer", "enum": [0]},
        "auth_uuid": {"type": "string", "format": "uuid"},
        "auth_client_id": {"type": "string"},
        "auth_app_id": {"pattern": "^1$"},
        "auth_app_name": {"pattern": "an app"},
        "auth_pkce_method": {"type": "null"},
        "auth_share_demographic_scopes": {"pattern": "^$"},
        "auth_require_demographic_scopes": {"pattern": "^True$"},
    },
    "required": ["type", "auth_status", "auth_status_code", "user", "application",
                 "share_demographic_scopes", "scopes", "allow", "access_token_delete_cnt",
                 "refresh_token_delete_cnt", "data_access_grant_delete_cnt", "auth_uuid",
                 "auth_client_id", "auth_app_id", "auth_app_name", "auth_pkce_method",
                 "auth_share_demographic_scopes", "auth_require_demographic_scopes"]
}

FHIR_AUTH_POST_FETCH_LOG_SCHEMA = {
    "title": "FhirAuthPostFetchLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "fhir_auth_post_fetch"},
        "uuid": {"type": "string"},
        "includeAddressFields": {"pattern": "False"},
        "path": {"pattern": "patient search"},
        "start_time": {"type": "string"},
        "code": {"type": "integer", "enum": [200]},
        "size": {"type": "integer"},
        "elapsed": {"type": "number"},
    },
    "required": ["type", "uuid", "includeAddressFields", "path", "start_time", "code", "size", "elapsed"]
}

FHIR_AUTH_PRE_FETCH_LOG_SCHEMA = {
    "title": "FhirAuthPreFetchLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "fhir_auth_pre_fetch"},
        "uuid": {"type": "string"},
        "includeAddressFields": {"pattern": "False"},
        "path": {"pattern": "patient search"},
        "start_time": {"type": "string"},
    },
    "required": ["type", "uuid", "includeAddressFields", "path", "start_time"]
}

FHIR_POST_FETCH_LOG_SCHEMA = {
    "title": "FhirPostFetchLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "fhir_post_fetch"},
        "uuid": {"type": "string"},
        "fhir_id": {"pattern": "-20140000008325"},
        "includeAddressFields": {"pattern": "False"},
        "user": {"pattern": "patientId:-20140000008325"},
        "application": {"type": "object",
                        "properties": {
                            "id": {"pattern": "1"},
                            "name": {"pattern": "John_Smith_test"},
                            "user": {"type": "object",
                                     "properties": {
                                         "id": {"pattern": "1"}}}}},
        "path": {"pattern": "/v1/fhir/Patient"},
        "start_time": {"type": "string"},
        "code": {"type": "integer", "enum": [200]},
        "size": {"type": "integer"},
        "elapsed": {"type": "number"},
    },
    "required": ["type", "uuid", "fhir_id", "includeAddressFields", "user",
                 "application", "path", "start_time", "code", "size", "elapsed"]
}

FHIR_PRE_FETCH_LOG_SCHEMA = {
    "title": "FhirPreFetchLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "fhir_pre_fetch"},
        "uuid": {"type": "string"},
        "fhir_id": {"pattern": "-20140000008325"},
        "includeAddressFields": {"pattern": "False"},
        "user": {"pattern": "patientId:-20140000008325"},
        "application": {"type": "object",
                        "properties": {
                            "id": {"pattern": "1"},
                            "name": {"pattern": "John_Smith_test"},
                            "user": {"type": "object",
                                     "properties": {"id": {"pattern": "1"}}}}},
        "path": {"pattern": "/v1/fhir/Patient"},
        "start_time": {"type": "string"},
    },
    "required": ["type", "uuid", "fhir_id", "includeAddressFields", "user", "application", "path", "start_time"]
}

MATCH_FHIR_ID_LOG_SCHEMA = {
    "title": "MatchFhirIdLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "fhir.server.authentication.match_fhir_id"},
        "auth_uuid": {"type": "null"},
        "auth_app_id": {"type": "null"},
        "auth_app_name": {"type": "null"},
        "auth_client_id": {"type": "null"},
        "auth_pkce_method": {"type": "null"},
        "fhir_id": {"pattern": "-20140000008325"},
        "hicn_hash": {"pattern": "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948"},
        "mbi_hash": {"pattern": "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28"},
        "match_found": {"type": "boolean"},
        "hash_lookup_type": {"pattern": "M"},
        "hash_lookup_mesg": {"pattern": "FOUND beneficiary via mbi_hash"},
    },
    "required": ["type", "auth_uuid", "auth_app_id", "auth_app_name", "auth_client_id",
                 "auth_pkce_method", "fhir_id", "hicn_hash", "mbi_hash", "match_found", "hash_lookup_type",
                 "hash_lookup_mesg"]
}

MYMEDICARE_CB_CREATE_BENE_LOG_SCHEMA = {
    "title": "MyMedicareCbCreateBeneLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "mymedicare_cb:create_beneficiary_record"},
        "status": {"pattern": "OK"},
        "username": {"pattern": "00112233-4455-6677-8899-aabbccddeeff"},
        "fhir_id": {"pattern": "-20140000008325"},
        "user_mbi_hash": {"pattern": "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28"},
        "user_hicn_hash": {"pattern": "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948"},
        "mesg": {"pattern": "CREATE beneficiary record"},
    },
    "required": ["type", "status", "username", "fhir_id", "user_mbi_hash", "user_hicn_hash", "mesg"]
}

MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA = {
    "title": "MyMedicareCbGetUpdateBeneLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "mymedicare_cb:get_and_update_user"},
        "status": {"pattern": "OK"},
        "fhir_id": {"pattern": "-20140000008325"},
        "hicn_hash": {"pattern": "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948"},
        "mbi_hash": {"pattern": "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28"},
        "hash_lookup_type": {"pattern": "M"},
        "crosswalk": {"type": "object",
                      "properties": {
                          "id": {"type": "integer"},
                          "user_hicn_hash": {"pattern": "f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948"},
                          "user_mbi_hash": {"pattern": "4da2e5f86b900604651c89e51a68d421612e8013b6e3b4d5df8339d1de345b28"},
                          "fhir_id": {"pattern": "-20140000008325"},
                          "user_id_type": {"pattern": "M"}}},
        "mesg": {"pattern": "CREATE beneficiary record"},
    },
    "required": ["type", "status", "fhir_id", "hicn_hash", "mbi_hash", "crosswalk", "mesg"]
}

REQUEST_RESPONSE_MIDDLEWARE_LOG_SCHEMA = {
    "title": "RequestResponseLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "request_response_middleware"},
        "size": {"type": "integer"},
        "start_time": {"type": "number"},
        "end_time": {"type": "number"},
        "ip_addr": {"type": "string", "format": "ip-address"},
        "request_uuid": {"type": "string", "format": "uuid"},
        "req_user_id": {"type": "integer", "enum": [1]},
        "req_user_username": {"pattern": "00112233-4455-6677-8899-aabbccddeeff"},
        "req_fhir_id": {"pattern": "-20140000008325"},
        "auth_crosswalk_action": {"pattern": "C"},
        "path": {"pattern": "/mymedicare/sls-callback"},
        "request_method": {"pattern": "GET"},
        "request_scheme": {"pattern": "http"},
        "user": {"pattern": "00112233-4455-6677-8899-aabbccddeeff"},
        "fhir_id": {"pattern": "-20140000008325"},
        "response_code": {"type": "integer", "enum": [400]},
    },
    "required": ["type", "size", "start_time", "end_time", "ip_addr", "request_uuid",
                 "req_user_id", "req_user_username", "req_fhir_id", "auth_crosswalk_action",
                 "path", "request_method", "request_scheme", "user", "fhir_id", "response_code"]
}

SLSX_TOKEN_LOG_SCHEMA = {
    "title": "SlsxTokenLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "SLSx_token"},
        "uuid": {"type": "string"},
        "path": {"pattern": "/sso/session"},
        "auth_token": {"type": "string"},
        "code": {"type": "integer", "enum": [200]},
        "size": {"type": "integer"},
        "start_time": {"type": "string"},
        "elapsed": {"type": "number"},
    },
    "required": ["type", "uuid", "path", "auth_token", "code", "size", "start_time", "elapsed"]
}

SLSX_USERINFO_LOG_SCHEMA = {
    "title": "SlsxUserInfoLogSchema",
    "type": "object",
    "properties": {
        "type": {"pattern": "SLSx_userinfo"},
        "uuid": {"type": "string"},
        "path": {"pattern": "/v1/users/00112233-4455-6677-8899-aabbccddeeff"},
        "sub": {"pattern": "00112233-4455-6677-8899-aabbccddeeff"},
        "code": {"type": "integer", "enum": [200]},
        "size": {"type": "integer"},
        "start_time": {"type": "string"},
        "elapsed": {"type": "number"},
    },
    "required": ["type", "uuid", "path", "sub", "code", "size", "start_time", "elapsed"]
}
