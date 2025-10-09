HOME_PAGE = "home.html"
RESULTS_PAGE = "results.html"

ENDPOINT_URL_FMT = {
    "userinfo": "{}/{}/connect/userinfo",
    "patient": "{}/{}/fhir/Patient/{}?_format=json",
    "eob": "{}/{}/fhir/ExplanationOfBenefit/?_format=json",
    "coverage": "{}/{}/fhir/Coverage/?_format=json",
}

NAV_URI_FMT = "{}&_count={}&startIndex={}&{}={}"
