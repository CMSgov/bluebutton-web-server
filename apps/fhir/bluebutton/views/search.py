import copy
from jsonpath_ng.ext import parse as ext_parse
from rest_framework import (permissions)
from rest_framework.response import Response
from voluptuous import (
    Required,
    All,
    Match,
    Range,
    Coerce,
    Schema,
    REMOVE_EXTRA,
)

from apps.fhir.bluebutton.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.views.home import get_response_json
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from ..permissions import (SearchCrosswalkPermission, ResourcePermission, ApplicationActivePermission)
from apps.fhir.bluebutton.views.b64card import B64_BLU_CARD, B64_RED_BLU_CARD, B64_BLU_CARD_BG, B64_HUMANA_PTD


# image mapping to part A, B, C, D
# A: B64_BLU_CARD_BG large vertical figma card as background
# B: B64_RED_BLU_CARD classic medicare card image
# C: B64_BLU_CARD horizontal figma card
# D: B64_HUMANA_PTD medicare RX humana part D card
INS_TYPE2CARD = {
    "Part A": ''.join(B64_BLU_CARD_BG.splitlines()),
    "Part B": ''.join(B64_RED_BLU_CARD.splitlines()),
    "Part C": ''.join(B64_BLU_CARD.splitlines()),
    "Part D": ''.join(B64_HUMANA_PTD.splitlines())
}

C4BB_COVERAGE_PROFILE_URL = "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-Coverage"

C4DIC_COVERAGE_PROFILE_URL = "http://hl7.org/fhir/us/insurance-card/StructureDefinition/C4DIC-Coverage"

C4DIC_SUPPORTING_IMAGE_EXT = {
    "extension": [
        {
            "url": "description",
            "valueString": "Beneficiary's proof of insurance"
        },
        {
            "url": "image",
            "valueAttachment": {
                "contentType": "image/png",
                "data": "<replace with base64 encoded iamge png here>"
            }
        },
        {
            "url": "label",
            "valueString": "CMS Insurance card"
        }
    ],
    "url": "http://hl7.org/fhir/us/insurance-card/StructureDefinition/C4DIC-SupportingImage-extension"
}


# POC helper
def lookup_by_path(expr, json_obj):
    jsonpath_expr = ext_parse(expr)
    return jsonpath_expr.find(json_obj)


# POC helper
def lookup_1_and_get(expr, attribute, json_obj):
    r = lookup_by_path(expr, json_obj)
    if r and isinstance(r, list):
        return r[0].value[attribute]


# POC helper: generate supporting image extension per coverage class type
def get_supporting_image_extension(b64encoded: str):
    ext = copy.deepcopy(C4DIC_SUPPORTING_IMAGE_EXT)
    for e in ext['extension']:
        if e['url'] == 'image':
            e['valueAttachment']['data'] = b64encoded
            break
    return ext


# POC helper
def enrich_supporting_image(resp: Response):
    for e in resp.data['entry']:
        profiles = e['resource']['meta']['profile']
        # the search result with _profile=http://hl7.org/fhir/us/insurance-card/StructureDefinition/C4DIC-Coverage
        # still return C4BB-Coverage, so need to force it into C4DIC-Coverage
        # if C4DIC_COVERAGE_PROFILE_URL in profiles:

        if C4BB_COVERAGE_PROFILE_URL == profiles[0]:
            e['resource']['meta']['profile'][0] = C4DIC_COVERAGE_PROFILE_URL

        extensions = e['resource']['extension']
        class_type = lookup_1_and_get("$.resource.class[?(@.type.coding[0].code=='plan')]", "value", e)
        class_type = "Part A" if class_type is None else class_type
        extensions.append(get_supporting_image_extension(INS_TYPE2CARD[class_type]))

    return resp


class SearchView(FhirDataView):
    # Base class for FHIR resource search views

    # BB2-149 note, check authenticated first, then app active etc.
    permission_classes = [
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        ResourcePermission,
        SearchCrosswalkPermission,
        DataAccessGrantPermission,
        TokenHasProtectedCapability,
    ]

    # Regex to match a valid _lastUpdated value that can begin with lt, le, gt and ge operators
    REGEX_LASTUPDATED_VALUE = r'^((lt)|(le)|(gt)|(ge)).+'

    QUERY_TRANSFORMS = {
        'count': '_count',
    }

    QUERY_SCHEMA = {
        Required('startIndex', default=0): Coerce(int),
        Required('_count', default=DEFAULT_PAGE_SIZE): All(Coerce(int), Range(min=0, max=MAX_PAGE_SIZE)),
        '_lastUpdated': [Match(REGEX_LASTUPDATED_VALUE, msg="the _lastUpdated operator is not valid")]
    }

    def __init__(self, version=1):
        self.resource_type = None
        super().__init__(version)

    def initial(self, request, *args, **kwargs):
        return super().initial(request, self.resource_type, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, self.resource_type, *args, **kwargs)

    def build_url(self, resource_router, resource_type, *args, **kwargs):
        if resource_router.fhir_url.endswith('v1/fhir/'):
            # only if called by tests
            return "{}{}/".format(resource_router.fhir_url, resource_type)
        else:
            return "{}/{}/fhir/{}/".format(resource_router.fhir_url, 'v2' if self.version == 2 else 'v1',
                                           resource_type)


class SearchViewPatient(SearchView):
    # Class used for Patient resource search view

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Patient"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            '_id': request.crosswalk.fhir_id,
        }

    def get(self, request, *args, **kwargs):
        return_c4dic = False
        if return_c4dic:
            return Response(get_response_json("bfd-c4dic-patient-search"))
        else:
            return super().get(request, *args, **kwargs)


class SearchViewCoverage(SearchView):
    # Class used for Coverage resource search view

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Coverage"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            'beneficiary': 'Patient/' + request.crosswalk.fhir_id,
        }

    def get(self, request, *args, **kwargs):
        profile = request.query_params.get('_profile', '')
        return_c4dic = False
        if return_c4dic and profile == C4DIC_COVERAGE_PROFILE_URL:
            return Response(get_response_json("bfd-c4dic-coverage-search"))
        else:
            resp = super().get(request, *args, **kwargs)
            # C4DIC POC: inject c4dic supportingImage extension if the _profile indicate C4DIC Coverage search
            return enrich_supporting_image(resp) if profile == C4DIC_COVERAGE_PROFILE_URL else resp


class SearchViewExplanationOfBenefit(SearchView):
    # Class used for ExplanationOfBenefit resource search view

    # Regex to match a valid type value
    REGEX_TYPE_VALUE = r"(carrier)|" + \
                       r"(pde)|" + \
                       r"(dme)|" + \
                       r"(hha)|" + \
                       r"(hospice)|" + \
                       r"(inpatient)|" + \
                       r"(outpatient)|" + \
                       r"(snf)|" + \
                       r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|)|" + \
                       r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|carrier)|" + \
                       r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|pde)|" + \
                       r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|dme)|" + \
                       r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|hha)|" + \
                       r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|hospice)|" + \
                       r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|inpatient)|" + \
                       r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|outpatient)|" + \
                       r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|snf)"

    # Regex to match a list of comma separated type values with IGNORECASE
    REGEX_TYPE_VALUES_LIST = r'(?i)^((' + REGEX_TYPE_VALUE + r')\s*,*\s*)+$'

    # Regex to match a valid service-date value that can begin with lt, le, gt and ge operators
    REGEX_SERVICE_DATE_VALUE = r'^((lt)|(le)|(gt)|(ge)).+'

    # Add type parameter to schema only for EOB
    QUERY_SCHEMA = {**SearchView.QUERY_SCHEMA,
                    'type': Match(REGEX_TYPE_VALUES_LIST, msg="the type parameter value is not valid"),
                    'service-date': [Match(REGEX_SERVICE_DATE_VALUE, msg="the service-date operator is not valid")]
                    }

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "ExplanationOfBenefit"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            'patient': request.crosswalk.fhir_id,
        }

    def filter_parameters(self, request):
        params = self.map_parameters(request.query_params.dict())
        # Get list from _lastUpdated QueryDict(), since it can have multi params
        params['_lastUpdated'] = request.query_params.getlist('_lastUpdated')
        # Get list from service-date QueryDict(), since it can have multi params
        service_dates = request.query_params.getlist('service-date')
        if service_dates:
            params['service-date'] = service_dates

        schema = Schema(
            getattr(self, "QUERY_SCHEMA", {}),
            extra=REMOVE_EXTRA)
        return schema(params)
