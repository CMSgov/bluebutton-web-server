from django.http import JsonResponse
import apps.logging.request_logger as bb2logging
import logging
from apps.versions import Versions

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

HOME_PAGE = 'home.html'
RESULTS_PAGE = 'results.html'

# Used as a default patient ID in the EndpointUrl formatter.
# It should be impossible for us to see it, but it forces
# an error condition if we do.
BAD_PATIENT_ID = 'INTERNAL_BAD_PATIENT_ID'


class EndpointFormatException(Exception):
    """Exception for endpoint formatting errors.

    The goal of endpoint formatting is to make it *hard* to end up with an exception.
    Therefore, this exception should only be thrown in the situation where a URI was asked
    to be formatted, but no matching case could be found.
    """
    pass


class EndpointUrl:
    userinfo = "userinfo"
    patient = "patient"
    explanation_of_benefit = "eob"
    coverage = "coverage"
    digital_insurance_card = "digital_insurance_card"
    nav = "nav"

    @staticmethod
    def fmt(name: str, uri: str, version: int, patient: str = BAD_PATIENT_ID):
        version_as_string = Versions.as_str(version)
        match name:
            case EndpointUrl.userinfo:
                return f'{uri}/{version_as_string}/connect/userinfo'
            case EndpointUrl.patient:
                if patient is None or patient == BAD_PATIENT_ID:
                    logger.error('EndpointUrl format called with invalid patient id')
                    raise EndpointFormatException('EndpointUrl format called with invalid patient id')
                return f'{uri}/{version_as_string}/fhir/Patient/{patient}?_format=application/fhir+json'
            case EndpointUrl.explanation_of_benefit:
                return f'{uri}/{version_as_string}/fhir/ExplanationOfBenefit/?_format=application/fhir+json'
            case EndpointUrl.coverage:
                return f'{uri}/{version_as_string}/fhir/Coverage/?_format=application/fhir+json'
            case EndpointUrl.digital_insurance_card:
                return f'{uri}/{version_as_string}/fhir/DigitalInsuranceCard/?_format=application/fhir+json'
            case _:
                logger.error(f'Could not match name in EndpointUrl: {name}')

        # If we are asked to format something that doesn't exist, raise an exception. This situation should
        # never occur, and therefore we want something to break.
        raise EndpointFormatException(f'Could not format URI name[{name}] uri[{uri}] version[{version_as_string}]')

    @staticmethod
    def nav_uri(uri, count, start_index, id_type=None, id=None):
        return f'{uri}&_count={count}&startIndex={start_index}&{id_type}={id}'


class ResponseErrors:
    def MissingTokenError(self, msg):
        return JsonResponse({
            'error': f'Failed to get token from {msg}',
            'code': 'MissingTokenError',
            'help': 'Try authorizing again'},
            500)

    def InvalidClient(self, msg):
        return JsonResponse({
            'error': f'Failed to get token from {msg}',
            'code': 'InvalidClient',
            'help': 'Try authorizing again'},
            500)

    def MissingPatientError(self):
        return JsonResponse({
            'error': 'No patient found in token; only synthetic benficiares can be used.',
            'code': 'MissingPatientError',
            'help': 'Try authorizing again'},
            500)

    def NonSyntheticTokenError(self, msg):
        return JsonResponse({
            'error': f'Failed token is for a non-synthetic patient_id = {msg}',
            'code': 'NonSyntheticTokenError',
            'help': 'Try authorizing again.'
        }, 403)

    def MissingCallbackVersionContext(self, msg):
        return JsonResponse({
            'error': 'Missing API version in callback session',
            'code': 'MissingCallbackVersion',
            'help': 'Try authorizing again'
        }, 500)
