import json
import logging


"""
  Logger functions for fhir/server module
"""

logger = logging.getLogger('hhs_server.%s' % __name__)


# For use in authentication.log_match_fhir_id()
def log_match_fhir_id(fhir_id, mbi_hash, hicn_hash,
                      match_found, hash_lookup_type, hash_lookup_mesg):
    '''
        Logging for "fhir.server.authentication.match_fhir_id" type
        used in match_fhir_id()
    '''
    logger.info(json.dumps({
        "type": "fhir.server.authentication.match_fhir_id",
        "fhir_id": fhir_id,
        "mbi_hash": mbi_hash,
        "hicn_hash": hicn_hash,
        "match_found": match_found,
        "hash_lookup_type": hash_lookup_type,
        "hash_lookup_mesg": hash_lookup_mesg,
    }))
