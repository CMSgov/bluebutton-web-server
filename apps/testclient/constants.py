HOME_PAGE = "home.html"
RESULTS_PAGE = "results.html"

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
            case EndpointUrl.userinfo: return f"{uri}/{version}/connect/userinfo"
            case EndpointUrl.patient: return f"{uri}/{version}/fhir/Patient/{patient}?_format=json"
            case EndpointUrl.explanation_of_benefit: return f"{uri}/{version}/ExplanationOfBenefit/?_format=json"
            case EndpointUrl.coverage: return f"{uri}/{version}/Coverage/?_format=json"

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
