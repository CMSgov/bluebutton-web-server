# We do not want to track metrics for the following app names
APP_NAMES_TO_IGNORE = ['TestApp', 'BlueButton Client (Test - Internal Use Only)', 'MyMedicare PROD', 'new-relic', 'datadog']

REQUEST_RESPONSE_MIDDLEWARE_TYPE = 'request_response_middleware'

AUDIT_EVENT_TYPES = [
    "Authentication:start",
    "Authentication:success",
    "Authorization",
    "AccessToken"
]

REDIRECT_STATUS_CODE = 302
OK_STATUS_CODE = 200


# Various helper functions
def to_int(value):
    if value == None or value == "":
        return None
    return int(value)

def is_real(fhir_id_v2, fhir_id_v3):
    """
    True if either FHIR ID indicates a real beneficiary.
    Mirrors SQL: fhir_id_v2 > 0 OR COALESCE(fhir_id_v3, 0) > 0
    """
    v2 = to_int(fhir_id_v2)
    v3 = to_int(fhir_id_v3)
    v3_val = v3 if v3 != None else 0
    return (v2 != None and v2 > 0) or v3_val > 0

def response_code_equals(response_code, val):
    return to_int(response_code) == val

def response_code_not_equals(response_code, val):
    return to_int(response_code) != val

def response_code_in(response_code, vals):
    return to_int(response_code) in vals

def response_code_not_in(response_code, vals):
    return to_int(response_code) not in vals

def response_code_range(response_code, low, high):
    rc = to_int(response_code)
    if rc == None:
        return False
    return (low <= rc and rc < high)

def response_code_gte(response_code, low):
    rc = to_int(response_code)
    if rc == None:
        return False
    return rc >= low

def path_matches_versioned_token(path):
    for v in ["v1", "v2", "v3"]:
        if path.startswith("/" + v + "/o/token"):
            return True
    return False

def path_matches_authorize_prefix(path):
    for v in ["v1", "v2", "v3"]:
        if path.startswith("/" + v + "/o/authorize/"):
            return True
    return False

def path_matches_authorize_full(path):
    for v in ["v1", "v2", "v3"]:
        prefix = "/" + v + "/o/authorize/"
        if path.startswith(prefix) and path.endswith("/") and len(path) > len(prefix):
            return True
    return False

def tag_source_parameter_shared_systems_check(qparam_source, qparam_tag):
    """
    Starlark equivalent of:
        LOWER(qparam_source) LIKE '%fiss%' OR ... OR
        qparam_tag LIKE '%https://bluebutton.cms.gov/fhir/CodeSystem/System-Type|SharedSystem%'
    """
    source_lower = qparam_source.lower() if qparam_source != None else ""
    tag = qparam_tag if qparam_tag != None else ""

    return (
        "fiss" in source_lower or
        "mcs" in source_lower or
        "vms" in source_lower or
        "map" in source_lower or
        "cwf" in source_lower or
        "https://bluebutton.cms.gov/fhir/CodeSystem/System-Type|SharedSystem" in tag
    )

def evaluate_request_response_metrics(tags):
    # Specifically analyze logs with type = 'request_response_middleware'
    matched = []

    path = tags.get("path") or ""
    request_method = tags.get("request_method") or ""
    response_code = tags.get("response_code")
    fhir_id_v2 = tags.get("fhir_id_v2")
    fhir_id_v3 = tags.get("fhir_id_v3")
    lastupdated = tags.get("req_qparam_lastupdated") or ""
    auth_grant_type = tags.get("auth_grant_type") or ""
    sdk_header = tags.get("req_header_bluebutton_sdk") or ""
    qparam_source = tags.get("req_qparam__source") or ""
    qparam_tag = tags.get("req_qparam__tag") or ""
    patient_match_found = tags.get("patient_match_found") or ""

    # FHIR Resource call stats tracking
    # Top level conditional used in each real call, then check if real beneficiary or not, then check path
    if request_method == "GET" and response_code_equals(response_code, OK_STATUS_CODE):
        if is_real(fhir_id_v2, fhir_id_v3):
            # V1 Real Beneficiaries
            if path.startswith("/v1/fhir"):
                matched.append("app_fhir_v1_call_real_count")

            if path.startswith("/v1/fhir/ExplanationOfBenefit"):
                matched.append("app_fhir_v1_eob_call_real_count")

            if path.startswith("/v1/fhir/Coverage"):
                matched.append("app_fhir_v1_coverage_call_real_count")

            if path.startswith("/v1/fhir/Patient"):
                matched.append("app_fhir_v1_patient_call_real_count")

            if path.startswith("/v1/fhir/ExplanationOfBenefit") and lastupdated != "":
                matched.append("app_fhir_v1_eob_since_call_real_count")

            if path.startswith("/v1/fhir/Coverage") and lastupdated != "":
                matched.append("app_fhir_v1_coverage_since_call_real_count")

            # V2 Real Beneficiaries
            if path.startswith("/v2/fhir"):
                matched.append("app_fhir_v2_call_real_count")

            if path.startswith("/v2/fhir/ExplanationOfBenefit"):
                matched.append("app_fhir_v2_eob_call_real_count")

            if path.startswith("/v2/fhir/Coverage"):
                matched.append("app_fhir_v2_coverage_call_real_count")

            if path.startswith("/v2/fhir/Patient"):
                matched.append("app_fhir_v2_patient_call_real_count")

            if path.startswith("/v2/fhir/ExplanationOfBenefit") and lastupdated != "":
                matched.append("app_fhir_v2_eob_since_call_real_count")

            if path.startswith("/v2/fhir/Coverage") and lastupdated != "":
                matched.append("app_fhir_v2_coverage_since_call_real_count")

            # V3 Real Beneficiaries
            if path.startswith("/v3/fhir"):
                matched.append("app_fhir_v3_call_real_count")

            if path.startswith("/v3/fhir/ExplanationOfBenefit"):
                matched.append("app_fhir_v3_eob_call_real_count")

            if path.startswith("/v3/fhir/ExplanationOfBenefit") and tag_source_parameter_shared_systems_check(qparam_source, qparam_tag):
                matched.append("app_fhir_v3_eob_shared_systems_call_real_count")

            if path.startswith("/v3/fhir/Coverage"):
                matched.append("app_fhir_v3_coverage_call_real_count")

            if path.startswith("/v3/fhir/Patient"):
                matched.append("app_fhir_v3_patient_call_real_count")

            if path.startswith("/v3/fhir/ExplanationOfBenefit") and lastupdated != "":
                matched.append("app_fhir_v3_eob_since_call_real_count")

            if path.startswith("/v3/fhir/Coverage") and lastupdated != "":
                matched.append("app_fhir_v3_coverage_since_call_real_count")

            if path.startswith("/v3/fhir/Patient/") and "insurance-card" in path:
                matched.append("app_fhir_v3_generate_insurance_card_call_real_count")

        else:
            # V1 Synthetic Beneficiaries
            if path.startswith("/v1/fhir"):
                matched.append("app_fhir_v1_call_synthetic_count")

            if path.startswith("/v1/fhir/ExplanationOfBenefit"):
                matched.append("app_fhir_v1_eob_call_synthetic_count")

            if path.startswith("/v1/fhir/Coverage"):
                matched.append("app_fhir_v1_coverage_call_synthetic_count")

            if path.startswith("/v1/fhir/Patient"):
                matched.append("app_fhir_v1_patient_call_synthetic_count")

            if path.startswith("/v1/fhir/ExplanationOfBenefit") and lastupdated != "":
                matched.append("app_fhir_v1_eob_since_call_synthetic_count")

            if path.startswith("/v1/fhir/Coverage") and lastupdated != "":
                matched.append("app_fhir_v1_coverage_since_call_synthetic_count")

            # V2 Synthetic Beneficiaries
            if path.startswith("/v2/fhir"):
                matched.append("app_fhir_v2_call_synthetic_count")

            if path.startswith("/v2/fhir/ExplanationOfBenefit"):
                matched.append("app_fhir_v2_eob_call_synthetic_count")

            if path.startswith("/v2/fhir/Coverage"):
                matched.append("app_fhir_v2_coverage_call_synthetic_count")

            if path.startswith("/v2/fhir/Patient"):
                matched.append("app_fhir_v2_patient_call_synthetic_count")

            if path.startswith("/v2/fhir/ExplanationOfBenefit") and lastupdated != "":
                matched.append("app_fhir_v2_eob_since_call_synthetic_count")

            if path.startswith("/v2/fhir/Coverage") and lastupdated != "":
                matched.append("app_fhir_v2_coverage_since_call_synthetic_count")

            # V3 Synthetic Beneficiaries
            if path.startswith("/v3/fhir"):
                matched.append("app_fhir_v3_call_synthetic_count")

            if path.startswith("/v3/fhir/ExplanationOfBenefit"):
                matched.append("app_fhir_v3_eob_call_synthetic_count")

            if path.startswith("/v3/fhir/ExplanationOfBenefit") and tag_source_parameter_shared_systems_check(qparam_source, qparam_tag):
                matched.append("app_fhir_v3_eob_shared_systems_call_synthetic_count")

            if path.startswith("/v3/fhir/Coverage"):
                matched.append("app_fhir_v3_coverage_call_synthetic_count")

            if path.startswith("/v3/fhir/Patient"):
                matched.append("app_fhir_v3_patient_call_synthetic_count")

            if path.startswith("/v3/fhir/ExplanationOfBenefit") and lastupdated != "":
                matched.append("app_fhir_v3_eob_since_call_synthetic_count")

            if path.startswith("/v3/fhir/Coverage") and lastupdated != "":
                matched.append("app_fhir_v3_coverage_since_call_synthetic_count")

            if path.startswith("/v3/fhir/Patient/") and "insurance-card" in path:
                matched.append("app_fhir_v3_generate_insurance_card_call_synthetic_count")

    if path.startswith("/v1/fhir/metadata") and request_method == "GET" and response_code_equals(response_code, OK_STATUS_CODE):
        matched.append("app_fhir_v1_metadata_call_count")

    if path.startswith("/v2/fhir/metadata") and request_method == "GET" and response_code_equals(response_code, OK_STATUS_CODE):
        matched.append("app_fhir_v2_metadata_call_count")

    if path.startswith("/v3/fhir/metadata") and request_method == "GET" and response_code_equals(response_code, OK_STATUS_CODE):
        matched.append("app_fhir_v3_metadata_call_count")

    # Token request stats
    if request_method == "POST" and path_matches_versioned_token(path) and auth_grant_type == "refresh_token":
        if response_code_range(response_code, OK_STATUS_CODE, 300):
            matched.append("app_token_refresh_response_2xx_count")
        elif response_code_range(response_code, 400, 500):
            matched.append("app_token_refresh_response_4xx_count")
        elif response_code_gte(response_code, 500):
            matched.append("app_token_refresh_response_5xx_count")

    if request_method == "POST" and path_matches_versioned_token(path) and auth_grant_type == "authorization_code":
        if response_code_range(response_code, OK_STATUS_CODE, 300):
            matched.append("app_token_authorization_code_2xx_count")
        elif response_code_range(response_code, 400, 500):
            matched.append("app_token_authorization_code_4xx_count")
        elif response_code_gte(response_code, 500):
            matched.append("app_token_authorization_code_5xx_count")

    if request_method == "POST" and path_matches_versioned_token(path) and auth_grant_type == "client_credentials":
        if response_code_range(response_code, OK_STATUS_CODE, 300):
            matched.append("app_successful_client_credentials_call")
        else:
            matched.append("app_unsuccessful_client_credentials_call")
 
    if path_matches_versioned_token(path) and patient_match_found == True:
        matched.append("app_successful_patient_match_call")
    if path_matches_versioned_token(path) and patient_match_found == False:
        matched.append("app_unsuccessful_patient_match_call")

    # Auth flow stats
    if path_matches_authorize_prefix(path):
        matched.append("app_authorize_initial_count")

    if path == "/mymedicare/login" and response_code_equals(response_code, REDIRECT_STATUS_CODE):
        matched.append("app_medicare_login_redirect_ok_count")

    if path == "/mymedicare/login" and response_code_not_equals(response_code, REDIRECT_STATUS_CODE):
        matched.append("app_medicare_login_redirect_fail_count")

    if path == "/mymedicare/sls-callback" and response_code_equals(response_code, REDIRECT_STATUS_CODE):
        if is_real(fhir_id_v2, fhir_id_v3):
            matched.append("app_sls_callback_ok_real_count")
        else:
            matched.append("app_sls_callback_ok_synthetic_count")

    if path == "/mymedicare/sls-callback" and response_code_not_equals(response_code, REDIRECT_STATUS_CODE):
        matched.append("app_sls_callback_fail_count")

    if path_matches_authorize_full(path) and request_method == "GET" and response_code_in(response_code, [OK_STATUS_CODE, REDIRECT_STATUS_CODE]):
        if is_real(fhir_id_v2, fhir_id_v3):
            matched.append("app_approval_view_get_ok_real_count")
        else:
            matched.append("app_approval_view_get_ok_synthetic_count")

    if path_matches_authorize_full(path) and request_method == "GET" and response_code_not_in(response_code, [OK_STATUS_CODE, REDIRECT_STATUS_CODE]):
        matched.append("app_approval_view_get_fail_count")

    if path_matches_authorize_full(path) and request_method == "POST" and response_code_in(response_code, [OK_STATUS_CODE, REDIRECT_STATUS_CODE]):
        if is_real(fhir_id_v2, fhir_id_v3):
            matched.append("app_approval_view_post_ok_real_count")
        else:
            matched.append("app_approval_view_post_ok_synthetic_count")

    if path_matches_authorize_full(path) and request_method == "POST" and response_code_not_in(response_code, [OK_STATUS_CODE, REDIRECT_STATUS_CODE]):
        matched.append("app_approval_view_post_fail_count")

    if sdk_header == "python":
        matched.append("app_sdk_requests_python_count")

    if sdk_header == "node":
        matched.append("app_sdk_requests_node_count")

    return matched

def evaluate_audit_metrics(tags):
    # Specifically analyze log events with type equal to Authentication:start, Authentication:success, AccessToken or Authorization
    matched = []

    event_type = tags.get("type") or ""
    auth_status = tags.get("auth_status") or ""
    allow = tags.get("allow") or ""
    auth_grant_type = tags.get("auth_grant_type") or ""
    auth_action = tags.get("action") or ""
    auth_crosswalk_action = tags.get("auth_crosswalk_action") or ""
    auth_require_demographic_scopes = tags.get("auth_require_demographic_scopes") or ""
    share_demographic_scopes = tags.get("share_demographic_scopes") or ""
    sls_status = tags.get("sls_userinfo_status_code")
    auth_share_samhsa_data = tags.get("auth_share_samhsa_data") or ""
    path = tags.get("path") or ""

    # For Authorization/Authentication:success events
    crosswalk_fhir_id = tags.get("fhir_id_v2")
    crosswalk_fhir_id_v3 = tags.get("fhir_id_v3")

    if event_type == "Authorization":

        if auth_status == "OK" and allow == "True":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_ok_real_bene_count")
            else:
                matched.append("app_auth_ok_synthetic_bene_count")

        if auth_status == "FAIL":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_fail_or_deny_real_bene_count")
            else:
                matched.append("app_auth_fail_or_deny_synthetic_bene_count")


        if auth_status == "OK" and allow == "True" and auth_require_demographic_scopes == "True" and share_demographic_scopes == "True":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_demoscope_required_choice_sharing_real_bene_count")
            else:
                matched.append("app_auth_demoscope_required_choice_sharing_synthetic_bene_count")

        if auth_status == "OK" and allow == "True" and auth_require_demographic_scopes == "True" and share_demographic_scopes == "False":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_demoscope_required_choice_not_sharing_real_bene_count")
            else:
                matched.append("app_auth_demoscope_required_choice_not_sharing_synthetic_bene_count")

        if allow == "False" and auth_require_demographic_scopes == "True":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_demoscope_required_choice_deny_real_bene_count")
            else:
                matched.append("app_auth_demoscope_required_choice_deny_synthetic_bene_count")

        if auth_status == "OK" and allow == "True" and auth_require_demographic_scopes == "False":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_demoscope_not_required_not_sharing_real_bene_count")
            else:
                matched.append("app_auth_demoscope_not_required_not_sharing_synthetic_bene_count")

        if allow == "False" and auth_require_demographic_scopes == "False":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_demoscope_not_required_deny_real_bene_count")
            else:
                matched.append("app_auth_demoscope_not_required_deny_synthetic_bene_count")

        if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3) and (path.startswith('/v1/o/authorize') or path.startswith('/v2/o/authorize')):
            matched.append("app_auth_v1_v2_user_clicks_connect_bene_count")

        if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3) and path.startswith('/v3/o/authorize'):
            matched.append("app_auth_v3_user_clicks_connect_bene_count")

        if auth_status == "OK" and (allow == "True" or allow == True) and (auth_share_samhsa_data == "True" or auth_share_samhsa_data == True):
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_samhsa_presented_sharing_real_bene_count")
            else:
                matched.append("app_auth_samhsa_presented_sharing_synthetic_bene_count")

        if auth_status == "OK" and (allow == "True" or allow == True) and (auth_share_samhsa_data == "False" or auth_share_samhsa_data == False):
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_samhsa_presented_not_sharing_real_bene_count")
            else:
                matched.append("app_auth_samhsa_presented_not_sharing_synthetic_bene_count")

        if auth_status == "OK" and (allow == "True" or allow == True) and auth_share_samhsa_data == "":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_auth_samhsa_not_presented_real_bene_count")
            else:           
                matched.append("app_auth_samhsa_not_presented_synthetic_bene_count")

    if event_type == "AccessToken":

        if auth_action == "authorized" and auth_grant_type == "refresh_token":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_token_refresh_for_real_bene_count")
            else:
                matched.append("app_token_refresh_for_synthetic_bene_count")

        if auth_grant_type == "authorization_code":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_token_authorization_code_for_real_bene_count")
            else:
                matched.append("app_token_authorization_code_for_synthetic_bene_count")

    if event_type == "Authentication:start":

        if response_code_equals(sls_status, OK_STATUS_CODE):
            matched.append("app_authentication_start_ok_count")
        else:
            matched.append("app_authentication_start_fail_count")

    if event_type == "Authentication:success":

        if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3) and (path == 'v1/mymedicare/sls-callback' or path == 'v2/mymedicare/sls-callback'):
            matched.append("app_auth_v1_v2_user_makes_it_to_permission_screen_bene_count")

        if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3) and path == 'v3/mymedicare/sls-callback':
            matched.append("app_auth_v3_user_makes_it_to_permission_screen_bene_count")

        if auth_crosswalk_action == "C":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_authentication_matched_new_bene_real_count")
            else:
                matched.append("app_authentication_matched_new_bene_synthetic_count")

        if auth_crosswalk_action == "R":
            if is_real(crosswalk_fhir_id, crosswalk_fhir_id_v3):
                matched.append("app_authentication_matched_returning_bene_real_count")
            else:
                matched.append("app_authentication_matched_returning_bene_synthetic_count")

    return matched

def summarize():
    # Entry point for app-summary ETL

    # Dictionary to track event counts grouped by metric/app
    # For each event that applies to a specific metric for an app,
    # We increment the count for that metric/app key
    accumulator = {}

    # List that will contain the summary rows that will be returned/written to itslog_summary
    returning_summary_rows = []

    events = query('events', 'SELECT * FROM itslog_events')

    for event in events:
    # for event_dict in EVENTS:
        event_dict = json.decode(event.get('value'))
        print("THE EVENT: ", event_dict)

        app_name = event_dict.get('app_name')
        app_id = event_dict.get('app_id')

        if not app_name or not app_id:
            continue

        app_tag = app_id + '.' + app_name

        if event_dict.get('type') == REQUEST_RESPONSE_MIDDLEWARE_TYPE:
            for metric in evaluate_request_response_metrics(event_dict):
                key = (metric, app_tag)
                accumulator[key] = accumulator.get(key, 0) + 1

        if event_dict.get('type') in AUDIT_EVENT_TYPES:
            for metric in evaluate_audit_metrics(event_dict):
                key = (metric, app_tag)
                accumulator[key] = accumulator.get(key, 0) + 1

    for (metric_tag, app_tag), count in accumulator.items():
        returning_summary_rows.append({
            "operation": metric_tag,
            "tags": app_tag,
            "value": str(count),
            "count": 1,
        })
    for row in returning_summary_rows:
        print("ROW: ", row)

    return returning_summary_rows

summarize()
