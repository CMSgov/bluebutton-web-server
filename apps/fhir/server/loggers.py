import json
import logging


"""
  Logger functions for fhir/server module
"""
match_fhir_id_logger = logging.getLogger('audit.authenticate.match_fhir_id')


# For use in authentication.log_match_fhir_id()
def log_match_fhir_id(auth_flow_dict, fhir_id, mbi_hash, hicn_hash,
                      match_found, hash_lookup_type, hash_lookup_mesg):
    '''
        Logging for "fhir.server.authentication.match_fhir_id" type
        used in match_fhir_id()
    '''
    match_fhir_id_logger.info(json.dumps({
        "type": "fhir.server.authentication.match_fhir_id",
        "auth_uuid": auth_flow_dict.get('auth_uuid', None),
        "auth_app_id": auth_flow_dict.get('auth_app_id', None),
        "auth_app_name": auth_flow_dict.get('auth_app_name', None),
        "auth_client_id": auth_flow_dict.get('auth_client_id', None),
        "auth_pkce_method": auth_flow_dict.get('auth_pkce_method', None),
        "fhir_id": fhir_id,
        "mbi_hash": mbi_hash,
        "hicn_hash": hicn_hash,
        "match_found": match_found,
        "hash_lookup_type": hash_lookup_type,
        "hash_lookup_mesg": hash_lookup_mesg,
    }))
