'''
  Endpoint schemas used for tests in apps/integration_tests/integration_test_fhir_resources.py
  See the following for information about the JSON Schema vocabulary: https://json-schema.org/
'''
USERINFO_SCHEMA = {
    "title": "Userinfo",
    'type': 'object',
    'properties': {
        'email': {'type': 'string'},
        'family_name': {'type': 'string'},
        'given_name': {'type': 'string'},
        'iat': {'type': 'string'},
        'name': {'type': 'string'},
        'patient': {'type': 'string'},
        'sub': {'type': 'string'}
    },
    'required': ['email', 'family_name', 'given_name',
                 'iat', 'name', 'patient', 'sub'],
}

FHIR_META_SCHEMA = {
    "title": "CapabilityStatement",
    'type': 'object',
    'properties': {
        "resourceType": {"type": "string"},
        "date": {"type": "string"},
        "publisher": {"type": "string"},
        "fhirVersion": {"type": "string"},
        "rest": {"type": "array"},
    },
    'required': ['resourceType', 'date', 'publisher',
                 'fhirVersion', 'rest'],
}

PATIENT_READ_SCHEMA = {
    "title": "PatientRead",
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "identifier": {"type": "array"},
        "name": {"type": "array"},
        "birthDate": {"type": "string"},
        "address": {"type": "array"}
    },
    "required": ["id", "resourceType", "identifier", "name", "birthDate", "address"]
}

PATIENT_SEARCH_SCHEMA = {
    "title": "PatientSearch",
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "entry": {"type": "array"}
    },
    "required": ["id", "resourceType", "entry"]
}

COVERAGE_READ_SCHEMA = {
    "title": "CoverageRead",
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "extension": {"type": "array"},
        "status": {"type": "string"},
        "type": {"type": "object"},
        "beneficiary": {"type": "object"},
        "grouping": {"type": "object"}
    },
    "required": ["id", "resourceType", "extension", "status", "type", "beneficiary", "grouping"]
}

COVERAGE_READ_SCHEMA_V2 = {
    "title": "CoverageRead",
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "extension": {"type": "array"},
        "status": {"type": "string"},
        "type": {"type": "object"},
        "beneficiary": {"type": "object"},
        "subscriberId": {"type": "string"},
        "relationship": {"type": "object"},
    },
    "required": ["id", "resourceType", "extension", "status", "type", "beneficiary", "subscriberId", "relationship"]
}

COVERAGE_SEARCH_SCHEMA = {
    "title": "CoverageSearch",
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "entry": {"type": "array"}
    },
    "required": ["id", "resourceType", "entry"]
}


EOB_READ_SCHEMA = {
    "title": "ExplenationofBenefitRead",
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "contained": {"type": "array"}
    },
    "required": ["id", "resourceType", "contained"]
}

EOB_READ_INPT_SCHEMA = {
    "title": "ExplenationofBenefitRead",
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "contained": {"type": "array"}
    },
    "required": ["id", "resourceType"]
}

EOB_SEARCH_SCHEMA = {
    "title": "ExplenationofBenefitsSearch",
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "entry": {"type": "array"},
    },
    "required": ["id", "resourceType", "entry"]
}
