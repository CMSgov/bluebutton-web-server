import re

# REGEX of paths that should be updated with auth flow info in hhs_oauth_server.request_logging.py
AUTH_FLOW_REQUEST_LOGGING_PATHS_REGEX = ('(^/v[1|2]/o/authorize/.*'
                                         '|^/mymedicare/login$|^/mymedicare/sls-callback$'
                                         '|^/v[1|2]/o/token/$)')

AUTHORIZE_INSTANCE_PARAM = 'uuid'

CODE_CHALLENGE_METHOD_S256 = 'S256'

DELETE_WITH_LIMIT = """DELETE FROM {table_name} WHERE auth_uuid IN
(SELECT auth_uuid FROM {table_name} WHERE created < '{age_date}'::date ORDER BY created LIMIT {limit_on_delete})"""

HEADERS = {
    'Remaining': 'X-RateLimit-Remaining',
    'Limit': 'X-RateLimit-Limit',
    'Reset': 'X-RateLimit-Reset',
}
PRINTABLE_SPECIAL_ASCII = "!\"#$%&'()*+,-/:;<=>?@[\\]^_`{|}~"

# List of value keys that are being tracked via request.session
SESSION_AUTH_FLOW_TRACE_KEYS = [
    'auth_uuid',
    'auth_client_id',
    'auth_grant_type',
    'auth_app_id',
    'auth_app_name',
    'auth_app_data_access_type',
    'auth_pkce_method',
    'auth_crosswalk_action',
    'auth_share_demographic_scopes',
    'auth_require_demographic_scopes',
    'auth_language'
]

SUPPORTED_VERSION_TEST_CASES = [
    {'url_path': '/v2/fhir/Patient/', 'expected': 2},
    # return 0 because v2 does not have a leading /
    {'url_path': 'v2/fhir/Patient/', 'expected': 0},
    {'url_path': '/v3/fhir/Coverage/', 'expected': 3},
    {'url_path': '/v3/fhir/Coverage/v2/', 'expected': 3},
]

TARGET_TABLE_COPY = 'dot_ext_authflowuuidcopy'
TARGET_TABLE = 'dot_ext_authflowuuid'

TOKEN_ENDPOINT_V1_KEY = 'token'
TOKEN_ENDPOINT_V2_KEY = 'token-v2'
TOKEN_ENDPOINT_V3_KEY = 'token-v3'

URL_REGEX = re.compile(
    r'^(https:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
    r'[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
)
