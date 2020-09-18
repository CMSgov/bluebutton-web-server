import json
import logging


"""
  Logger functions for mymedicare_cb module
"""
authenticate_logger = logging.getLogger('audit.authenticate.sls')
mymedicare_cb_logger = logging.getLogger('audit.authenticate.mymedicare_cb')


# For use in models.get_and_update_user()
def log_get_and_update_user(auth_flow_dict, status, user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, mesg):
    '''
        Logging for info or issue
        used in get_and_update_user()
        mesg = Description text.
    '''
    mymedicare_cb_logger.info(json.dumps({
        "type": "mymedicare_cb:get_and_update_user",
        "auth_uuid": auth_flow_dict.get('auth_uuid', None),
        "auth_app_id": auth_flow_dict.get('auth_app_id', None),
        "auth_app_name": auth_flow_dict.get('auth_app_name', None),
        "auth_client_id": auth_flow_dict.get('auth_client_id', None),
        "auth_pkce_method": auth_flow_dict.get('auth_pkce_method', None),
        "status": status,
        "fhir_id": fhir_id,
        "mbi_hash": mbi_hash,
        "hicn_hash": hicn_hash,
        "hash_lookup_type": hash_lookup_type,
        "crosswalk": {
            "id": user.crosswalk.id,
            "user_hicn_hash": user.crosswalk.user_hicn_hash,
            "user_mbi_hash": user.crosswalk.user_mbi_hash,
            "fhir_id": user.crosswalk.fhir_id,
            "user_id_type": user.crosswalk.user_id_type,
        },
        "mesg": mesg,
    }))


# For use in models.create_beneficiary_record()
def log_create_beneficiary_record(auth_flow_dict, status, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg):
    '''
        Logging for info or issue
        used in create_beneficiary_record()
        mesg = Description text.
    '''
    mymedicare_cb_logger.info(json.dumps({
        "type": "mymedicare_cb:create_beneficiary_record",
        "auth_uuid": auth_flow_dict.get('auth_uuid', None),
        "auth_app_id": auth_flow_dict.get('auth_app_id', None),
        "auth_app_name": auth_flow_dict.get('auth_app_name', None),
        "auth_client_id": auth_flow_dict.get('auth_client_id', None),
        "auth_pkce_method": auth_flow_dict.get('auth_pkce_method', None),
        "status": status,
        "username": username,
        "fhir_id": fhir_id,
        "user_mbi_hash": user_mbi_hash,
        "user_hicn_hash": user_hicn_hash,
        "mesg": mesg,
    }))


# For use in views.authenticate()
def log_authenticate_start(auth_flow_dict, sls_status, sls_status_mesg, sls_subject=None,
                           sls_mbi_format_valid=None, sls_mbi_format_msg=None,
                           sls_mbi_format_synthetic=None, sls_hicn_hash=None, sls_mbi_hash=None):

    authenticate_logger.info(json.dumps({
        "type": "Authentication:start",
        "auth_uuid": auth_flow_dict.get('auth_uuid', None),
        "auth_app_id": auth_flow_dict.get('auth_app_id', None),
        "auth_app_name": auth_flow_dict.get('auth_app_name', None),
        "auth_client_id": auth_flow_dict.get('auth_client_id', None),
        "auth_pkce_method": auth_flow_dict.get('auth_pkce_method', None),
        "sls_status": sls_status,
        "sls_status_mesg": sls_status_mesg,
        "sub": sls_subject,
        "sls_mbi_format_valid": sls_mbi_format_valid,
        "sls_mbi_format_msg": sls_mbi_format_msg,
        "sls_mbi_format_synthetic": sls_mbi_format_synthetic,
        "sls_hicn_hash": sls_hicn_hash,
        "sls_mbi_hash": sls_mbi_hash,
    }))


# For use in views.authenticate()
def log_authenticate_success(auth_flow_dict, sls_subject, user):
    authenticate_logger.info(json.dumps({
        "type": "Authentication:success",
        "auth_uuid": auth_flow_dict.get('auth_uuid', None),
        "auth_app_id": auth_flow_dict.get('auth_app_id', None),
        "auth_app_name": auth_flow_dict.get('auth_app_name', None),
        "auth_client_id": auth_flow_dict.get('auth_client_id', None),
        "auth_pkce_method": auth_flow_dict.get('auth_pkce_method', None),
        "auth_crosswalk_type": auth_flow_dict.get('auth_crosswalk_type', None),
        "sub": sls_subject,
        "user": {
            "id": user.id,
            "username": user.username,
            "crosswalk": {
                "id": user.crosswalk.id,
                "user_hicn_hash": user.crosswalk.user_hicn_hash,
                "user_mbi_hash": user.crosswalk.user_mbi_hash,
                "fhir_id": user.crosswalk.fhir_id,
                "user_id_type": user.crosswalk.user_id_type,
            },
        },
    }))
