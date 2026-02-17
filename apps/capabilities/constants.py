import re

FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES = '/v[123]/fhir/'
FHIR_PREFIX_CREATE_STARTER_SCOPES = 'fhir_prefix = "/v1/fhir/'

SUPPORTED_RESOURCES = [
    'Condition',
    'AllergyIntolerance',
    'Medication',
    'Observation',
    'FamilyMemberHistory',
    'Device',
    'Procedure',
    'Immunizations',
    'CarePlan',
    'DocumentReference',
]

URL_BIT_PATTERN = re.compile(r"\[.*\]")
