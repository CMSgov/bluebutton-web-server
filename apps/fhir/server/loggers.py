import apps.logging.request_logger as logging


"""
  Logger functions for fhir/server module
"""


def log_match_fhir_id(request, fhir_id, hicn_hash,
                      match_found, hash_lookup_type, hash_lookup_mesg):
    '''
        Logging for "fhir.server.authentication.match_fhir_id" type
        used in match_fhir_id()
    '''
    match_fhir_id_logger = logging.getLogger(logging.AUDIT_AUTHN_MATCH_FHIR_ID_LOGGER, request)
    match_fhir_id_logger.info({
        "type": "fhir.server.authentication.match_fhir_id",
        "fhir_id_v2": fhir_id,
        "hicn_hash": hicn_hash,
        "match_found": match_found,
        "hash_lookup_type": hash_lookup_type,
        "hash_lookup_mesg": hash_lookup_mesg,
    })
