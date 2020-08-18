import json


"""
  Logger functions for mymedicare_cb module
"""


# For use in models.get_and_update_user()
def log_get_and_update_user(logger, user, fhir_id, mbi_hash, hicn_hash, hash_lookup_type, mesg):
    '''
        Logging for info or issue
        used in get_and_update_user()
        mesg = Description text.
    '''
    logger.info(json.dumps({
        "type": "mymedicare_cb:get_and_update_user",
        "fhir_id": fhir_id,
        "mbi_hash": mbi_hash,
        "hicn_hash": hicn_hash,
        "hash_lookup_type": hash_lookup_type,
        "crosswalk":
            {
                "id": user.crosswalk.id,
                "user_hicn_hash": user.crosswalk.user_hicn_hash,
                "user_mbi_hash": user.crosswalk.user_mbi_hash,
                "fhir_id": user.crosswalk.fhir_id,
                "user_id_type": user.crosswalk.user_id_type,
            },
            "mesg": mesg,
    }))


# For use in models.create_beneficiary_record()
def log_create_beneficiary_record(logger, username, fhir_id, user_mbi_hash, user_hicn_hash, mesg):
    '''
        Logging for info or issue
        used in create_beneficiary_record()
        mesg = Description text.
    '''
    logger.info(json.dumps({
        "type": "mymedicare_cb:create_beneficiary_record",
        "username": username,
        "fhir_id": fhir_id,
        "user_mbi_hash": user_mbi_hash,
        "user_hicn_hash": user_hicn_hash,
        "mesg": mesg,
    }))


# For use in views.authenticate()
def log_authenticate_start(logger, sls_status, sls_status_mesg,
                           sls_subject=None,
                           sls_mbi_format_valid=None, sls_mbi_format_msg=None,
                           sls_mbi_format_synthetic=None, sls_hicn_hash=None, sls_mbi_hash=None):

    logger.info(json.dumps({
        "type": "Authentication:start",
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
def log_authenticate_success(logger, sls_subject, user):
    logger.info(json.dumps({
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
    }))
