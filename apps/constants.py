C4BB_PROFILE_URLS = {
    "COVERAGE": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-Coverage",
    "PATIENT": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-Patient",
    "INPATIENT": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Inpatient-Institutional",
    "OUTPATIENT": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Outpatient-Institutional",
    "PHARMACY": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Pharmacy",
    "NONCLINICIAN": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Professional-NonClinician",
}

CODE_CHALLENGE_METHOD_S256 = 'S256'

HHS_SERVER_LOGNAME_FMT = "hhs_server.{}"

MYMEDICARE_CB_GET_UPDATE_BENE_LOG_SCHEMA = {
    'title': 'MyMedicareCbGetUpdateBeneLogSchema',
    'type': 'object',
    'properties': {
        'type': {'type': 'string', 'pattern': '^mymedicare_cb:get_and_update_user_(initial_auth|refresh)$'},
        'status': {'type': 'string', 'pattern': '^OK$'},
        'subject': {
            'type': 'string',
            'pattern': '^00112233-4455-6677-8899-aabbccddeeff$',
        },
        'user_username': {
            'type': 'string',
            'pattern': '^00112233-4455-6677-8899-aabbccddeeff$',
        },
        'fhir_id_v2': {'type': 'string', 'pattern': '^-20140000008325$'},
        'hicn_hash': {
            'type': 'string',
            'pattern': '^f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948$',
        },
        'hash_lookup_type': {'type': 'string', 'pattern': '^M$'},
        'crosswalk': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'user_hicn_hash': {
                    'type': 'string',
                    'pattern': '^f7dd6b126d55a6c49f05987f4aab450deae3f990dcb5697875fd83cc61583948$',
                },
                'user_mbi': {
                    'type': 'string',
                    'pattern': '^1SA0A00AA00$',
                },
                'fhir_id_v2': {'type': 'string', 'pattern': '^-20140000008325$'},
                'user_id_type': {'type': 'string', 'pattern': '^M$'},
            },
        },
        'hicn_updated': {'enum': [False]},
        'mesg': {'type': 'string', 'pattern': '^CREATE beneficiary record$'},
        'request_uuid': {'type': 'string'},
        'crosswalk_before': {
            'type': 'object',
            'properties': {},
        },
    },
    'required': [
        'type',
        'status',
        'subject',
        'user_username',
        'fhir_id_v2',
        'hicn_hash',
        'crosswalk',
        'hicn_updated',
        'mesg',
        'request_uuid',
        'crosswalk_before',
    ],
}
