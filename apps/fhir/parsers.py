from rest_framework.parsers import JSONParser


class FHIRParser(JSONParser):
    media_type = 'application/fhir+json'
