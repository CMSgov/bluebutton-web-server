import apps.logging.request_logger as logging


"""
  Logger functions for mymedicare_cb module
"""
authenticate_logger = logging.getLogger('audit.authenticate.sls')
mymedicare_cb_logger = logging.getLogger('audit.authenticate.mymedicare_cb')


# For use in views.authenticate()
# def log_authenticate_start(auth_flow_dict, sls_status, sls_status_mesg, sls_subject=None,
#                            sls_mbi_format_valid=None, sls_mbi_format_msg=None,
#                            sls_mbi_format_synthetic=None, sls_hicn_hash=None,
#                            sls_mbi_hash=None, slsx_client=None):

#     log_dict = {
#         "type": "Authentication:start",
#         "sls_status": sls_status,
#         "sls_status_mesg": sls_status_mesg,
#         "sls_signout_status_code": slsx_client.signout_status_code,
#         "sls_token_status_code": slsx_client.token_status_code,
#         "sls_userinfo_status_code": slsx_client.userinfo_status_code,
#         "sls_validate_signout_status_code": slsx_client.validate_signout_status_code,
#         "sub": sls_subject,
#         "sls_mbi_format_valid": sls_mbi_format_valid,
#         "sls_mbi_format_msg": sls_mbi_format_msg,
#         "sls_mbi_format_synthetic": sls_mbi_format_synthetic,
#         "sls_hicn_hash": sls_hicn_hash,
#         "sls_mbi_hash": sls_mbi_hash,
#     }

#     # Update with auth flow session info
#     log_dict.update(auth_flow_dict if auth_flow_dict else {})

#     authenticate_logger.info(log_dict)


# For use in views.authenticate()
# def log_authenticate_success(auth_flow_dict, sls_subject, user):
#     log_dict = {
#         "type": "Authentication:success",
#         "sub": sls_subject,
#         "user": {
#             "id": user.id,
#             "username": user.username,
#             "crosswalk": {
#                 "id": user.crosswalk.id,
#                 "user_hicn_hash": user.crosswalk.user_hicn_hash,
#                 "user_mbi_hash": user.crosswalk.user_mbi_hash,
#                 "fhir_id": user.crosswalk.fhir_id,
#                 "user_id_type": user.crosswalk.user_id_type,
#             },
#         },
#     }

#     # Update with auth flow session info
#     log_dict.update(auth_flow_dict if auth_flow_dict else {})

#     authenticate_logger.info(log_dict)
