import apps.logging.request_logger as bb2logging
import logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

HOME_PAGE = "home.html"
RESULTS_PAGE = "results.html"

# Used as a default patient ID in the EndpointUrl formatter.
# It should be impossible for us to see it, but it forces
# an error condition if we do.
BAD_PATIENT_ID = "INTERNAL_BAD_PATIENT_ID"


class EndpointUrl:
    userinfo = "userinfo"
    patient = "patient"
    explanation_of_benefit = "eob"
    coverage = "coverage"
    # This is a special case?
    nav = "nav"

    def fmt(name: str, uri: str, version: str, patient: str = BAD_PATIENT_ID):
        match name:
            case EndpointUrl.userinfo:
                return f"{uri}/{version}/connect/userinfo"
            case EndpointUrl.patient:
                if patient is None or patient == BAD_PATIENT_ID:
                    logger.error(f"EndpointUrl format called with invalid patient id: {patient}")
                    raise
                return f"{uri}/{version}/fhir/Patient/{patient}?_format=json"
            case EndpointUrl.explanation_of_benefit:
                return f"{uri}/{version}/ExplanationOfBenefit/?_format=json"
            case EndpointUrl.coverage:
                return f"{uri}/{version}/Coverage/?_format=json"
            case _:
                logger.error(f"Could not match name in EndpointUrl: {name}")

                # Should not be possible to exit the match statement without a match.
                # Raise an error instead of returning? (The dictionary-based approach would similarly
                # fail badly, so this is not different behavior.)
        raise

    def nav_uri(uri, count, start_index, id_type=None, id=None):
        return f"{uri}&_count={count}&startIndex={start_index}&{id_type}={id}"

# ENDPOINT_URL_FMT = {
#     "userinfo": "{}/{}/connect/userinfo",
#     "patient": "{}/{}/fhir/Patient/{}?_format=json",
#     "eob": "{}/{}/fhir/ExplanationOfBenefit/?_format=json",
#     "coverage": "{}/{}/fhir/Coverage/?_format=json",
# }

# NAV_URI_FMT = "{}&_count={}&startIndex={}&{}={}"
