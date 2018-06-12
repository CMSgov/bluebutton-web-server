from rest_framework.renderers import JSONRenderer


class FHIRRenderer(JSONRenderer):
    media_type = 'application/fhir+json'
