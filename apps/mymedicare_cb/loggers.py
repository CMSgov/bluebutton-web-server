import json
import logging

from django.conf import settings


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
    log_dict = {
        "type": "mymedicare_cb:get_and_update_user",
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
    }
    # Update with auth flow session info
    if auth_flow_dict:
        log_dict.update(auth_flow_dict)

    if settings.LOG_JSON_FORMAT_PRETTY:
        mymedicare_cb_logger.info(json.dumps(log_dict, indent=2))
    else:
        mymedicare_cb_logger.info(json.dumps(log_dict))


# For use in models.create_beneficiary_record()
def log_create_beneficiary_record(auth_flow_dict, status, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg):
    '''
        Logging for info or issue
        used in create_beneficiary_record()
        mesg = Description text.
    '''
    log_dict = {
        "type": "mymedicare_cb:create_beneficiary_record",
        "status": status,
        "username": username,
        "fhir_id": fhir_id,
        "user_mbi_hash": user_mbi_hash,
        "user_hicn_hash": user_hicn_hash,
        "mesg": mesg,
    }
    # Update with auth flow session info
    if auth_flow_dict:
        log_dict.update(auth_flow_dict)

    if settings.LOG_JSON_FORMAT_PRETTY:
        mymedicare_cb_logger.info(json.dumps(log_dict, indent=2))
    else:
        mymedicare_cb_logger.info(json.dumps(log_dict))


# For use in views.authenticate()
def log_authenticate_start(auth_flow_dict, sls_status, sls_status_mesg, sls_subject=None,
                           sls_mbi_format_valid=None, sls_mbi_format_msg=None,
                           sls_mbi_format_synthetic=None, sls_hicn_hash=None,
                           sls_mbi_hash=None, slsx_client=None):

    log_dict = {
        "type": "Authentication:start",
        "sls_status": sls_status,
        "sls_status_mesg": sls_status_mesg,
        "sls_signout_status_code": slsx_client.signout_status_code,
        "sls_token_status_code": slsx_client.token_status_code,
        "sls_userinfo_status_code": slsx_client.userinfo_status_code,
        "sls_validate_signout_status_code": slsx_client.validate_signout_status_code,
        "sub": sls_subject,
        "sls_mbi_format_valid": sls_mbi_format_valid,
        "sls_mbi_format_msg": sls_mbi_format_msg,
        "sls_mbi_format_synthetic": sls_mbi_format_synthetic,
        "sls_hicn_hash": sls_hicn_hash,
        "sls_mbi_hash": sls_mbi_hash,
    }

    # Update with auth flow session info
    if auth_flow_dict:
        log_dict.update(auth_flow_dict)

    if settings.LOG_JSON_FORMAT_PRETTY:
        authenticate_logger.info(json.dumps(log_dict, indent=2))
    else:
        authenticate_logger.info(json.dumps(log_dict))


# For use in views.authenticate()
def log_authenticate_success(auth_flow_dict, sls_subject, user):
    log_dict = {
        "type": "Authentication:success",
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
    }
    # Update with auth flow session info
    if auth_flow_dict:
        log_dict.update(auth_flow_dict)

    if settings.LOG_JSON_FORMAT_PRETTY:
        authenticate_logger.info(json.dumps(log_dict, indent=2))
    else:
        authenticate_logger.info(json.dumps(log_dict))
