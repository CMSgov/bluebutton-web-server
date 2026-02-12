from apps.fhir.bluebutton.views.search import SearchViewExplanationOfBenefit
from apps.versions import Versions
from collections import namedtuple as NT
from django.conf import settings
from voluptuous import (
    All,
    Match,
    Range,
    Coerce,
)


ALLOWED_RESOURCE_TYPES = ['Patient', 'Coverage', 'ExplanationOfBenefit', 'Bundle']
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50

MBI_URL = 'http://hl7.org/fhir/sid/us-mbi'
MAX_RETRIES = 3
DEFAULT_SLEEP = 5

C4BB_PROFILE_URLS = {
    'INPATIENT': 'http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Inpatient-Institutional',
    'OUTPATIENT': 'http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Outpatient-Institutional',
    'PHARMACY': 'http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Pharmacy',
    'NONCLINICIAN': 'http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Professional-NonClinician',
}

C4BB_SYSTEM_TYPES = {
    'IDTYPE': 'http://hl7.org/fhir/us/carin-bb/CodeSystem/C4BBIdentifierType',
}

BAD_PARAMS_ACCEPTABLE_VERSIONS = [Versions.V1, Versions.V2]

READ_UPDATE_DELETE_PATIENT_URLS = {
    1: 'bb_oauth_fhir_patient_read_or_update_or_delete',
    2: 'bb_oauth_fhir_patient_read_or_update_or_delete_v2',
    3: 'bb_oauth_fhir_patient_read_or_update_or_delete_v3'
}

READ_UPDATE_DELETE_EOB_URLS = {
    1: 'bb_oauth_fhir_eob_read_or_update_or_delete',
    2: 'bb_oauth_fhir_eob_read_or_update_or_delete_v2',
    3: 'bb_oauth_fhir_eob_read_or_update_or_delete_v3'
}

READ_UPDATE_DELETE_COVERAGE_URLS = {
    1: 'bb_oauth_fhir_coverage_read_or_update_or_delete',
    2: 'bb_oauth_fhir_coverage_read_or_update_or_delete_v2',
    3: 'bb_oauth_fhir_coverage_read_or_update_or_delete_v3'
}

SEARCH_PATIENT_URLS = {
    1: 'bb_oauth_fhir_patient_search',
    2: 'bb_oauth_fhir_patient_search_v2',
    3: 'bb_oauth_fhir_patient_search_v3'
}

SEARCH_EOB_URLS = {
    1: 'bb_oauth_fhir_eob_search',
    2: 'bb_oauth_fhir_eob_search_v2',
    3: 'bb_oauth_fhir_eob_search_v3'
}

SEARCH_COVERAGE_URLS = {
    1: 'bb_oauth_fhir_coverage_search',
    2: 'bb_oauth_fhir_coverage_search_v2',
    3: 'bb_oauth_fhir_coverage_search_v3'
}

USERINFO_URLS = {
    1: 'openid_connect_userinfo',
    2: 'openid_connect_userinfo_v2',
    3: 'openid_connect_userinfo_v3',
}

FHIR_CONFORMANCE_URLS = {
    1: 'fhir_conformance_metadata',
    2: 'fhir_conformance_metadata_v2',
    3: 'fhir_conformance_metadata_v3',
}

ACCEPTED_PATIENT_QUERY_PARAMS = {
    'startIndex': Coerce(int, msg=None),
    '_count': All(
        Coerce(int, msg=None),
        Range(min=0, max=50, min_included=True, max_included=True, msg=None), msg=None
    ),
    '_lastUpdated': [Match('^((lt)|(le)|(gt)|(ge)).+', msg='the _lastUpdated operator is not valid')],
    '_id': str,
    'identifier': str
}
ACCEPTED_COVERAGE_QUERY_PARAMS = {
    'startIndex': Coerce(int, msg=None),
    '_count': All(
        Coerce(int, msg=None),
        Range(min=0, max=50, min_included=True, max_included=True, msg=None), msg=None
    ),
    '_lastUpdated': [Match('^((lt)|(le)|(gt)|(ge)).+', msg='the _lastUpdated operator is not valid')],
    'beneficiary': str
}
ACCEPTED_EOB_QUERY_PARAMS = {
    'startIndex': Coerce(int, msg=None),
    '_count': All(
        Coerce(int, msg=None),
        Range(min=0, max=50, min_included=True, max_included=True, msg=None), msg=None
    ),
    '_lastUpdated': [Match('^((lt)|(le)|(gt)|(ge)).+', msg='the _lastUpdated operator is not valid')],
    'type': Match('(?i)^(((carrier)|(pde)|(dme)|(hha)|(hospice)|(inpatient)|(outpatient)|(snf)|(https://bluebutton.cms.gov/'
                  'resources/codesystem/eob-type\\|)|(https://bluebutton.cms.gov/resources/codesystem/eob-type\\|carrier)|('
                  'https://bluebutton.cms.gov/resources/codesystem/eob-type\\|pde)|(https://bluebutton.cms.gov/resources/co'
                  'desystem/eob-type\\|dme)|(https://bluebutton.cms.gov/resources/codesystem/eob-type\\|hha)|(https://blueb'
                  'utton.cms.gov/resources/codesystem/eob-type\\|hospice)|(https://bluebutton.cms.gov/resources/codesystem/'
                  'eob-type\\|inpatient)|(https://bluebutton.cms.gov/resources/codesystem/eob-type\\|outpatient)|(https://b'
                  'luebutton.cms.gov/resources/codesystem/eob-type\\|snf))\\s*,*\\s*)+$',
                  msg='the type parameter value is not valid'),
    'service-date': [Match('^((lt)|(le)|(gt)|(ge)).+', msg='the service-date operator is not valid')],
    'patient': str,
    '_tag': SearchViewExplanationOfBenefit.validate_tag
}

# Introduced in bb2-4184
# Rudimentary tests to make sure endpoints exist and are returning
# basic responses that make sense. Not a deep test.
#
# PRECONDITION
# You must be on the VPN. Tested against TEST w.r.t. certs.

# Ensure that the status_code, version, and other attributes of the response are valid
Appropriate = NT('Status', 'url,version,status_code')
# Ensure the correct status_code is returned for a given endpoint
Status = NT('Status', 'url,status_code')
# These test cases ensure that certain fields are not present in the response for a given endpoint
MissingFields = NT('MissingFields', 'url,version,fields,status_code')

BASEURL = 'http://localhost:8000'
TESTS = [
    Appropriate('v1/connect/.well-known/openid-configuration', 'v1', 200),
    Appropriate('v2/connect/.well-known/openid-configuration', 'v2', 200),
    Appropriate('v3/connect/.well-known/openid-configuration', 'v3', 200),
    MissingFields('v3/fhir/.well-known/smart-configuration', 'v3', ['fhir_metadata_uri', 'userinfo_endpoint'], 200),
    Status('.well-known/openid-configuration', 200),
    Status('.well-known/openid-configuration-v2', 200)
]

PAGE_NOT_FOUND_TESTS = [
    Status('v3/connect/.well-known/openid-configuration', 404),
    Status('v3/fhir/.well-known/smart-configuration', 404),
    Status('v3/fhir/metadata', 404),
    Status('.well-known/openid-configuration-v3', 404),
]

ENFORCE_PARAM_VALIDATAION = 'handling=strict'

USER_SETTINGS = getattr(settings, "FHIR_SERVER", None)

DEFAULTS = {
    "FHIR_URL": None,
    "FHIR_URL_V3": None,
    "CLIENT_AUTH": False,
    "CERT_FILE": "",
    "KEY_FILE": "",
    "SERVER_VERIFY": False,
    "WAIT_TIME": 30,
    "VERIFY_SERVER": False,
}

# List of settings that cannot be empty
MANDATORY = (
    "FHIR_URL",
)
