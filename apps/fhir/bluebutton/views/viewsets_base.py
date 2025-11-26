from rest_framework import viewsets, permissions
from rest_framework.response import Response
from voluptuous import Schema, REMOVE_EXTRA

from apps.fhir.bluebutton.views.generic import FhirDataView


class ResourceViewSet(FhirDataView, viewsets.ViewSet):
    """Base FHIR resource ViewSet, would replace FhirDataView if we decide to go in that direction

    Args:
        FhirDataView: Base mixin, unchanged
        viewsets: django-rest-framework ViewSet base class
    """

    resource_type = None

    SEARCH_PERMISSION_CLASSES = (permissions.IsAuthenticated,)
    READ_PERMISSION_CLASSES = (permissions.IsAuthenticated,)

    def initial(self, request, *args, **kwargs):
        return super().initial(request, self.resource_type, *args, **kwargs)

    def get_permissions(self):
        action = getattr(self, 'action', None)
        if action == 'list':
            permission_classes = getattr(self, 'SEARCH_PERMISSION_CLASSES', self.SEARCH_PERMISSION_CLASSES)
        elif action == 'retrieve':
            permission_classes = getattr(self, 'READ_PERMISSION_CLASSES', self.READ_PERMISSION_CLASSES)
        else:
            permission_classes = (permissions.IsAuthenticated,)
        return [permission_class() for permission_class in permission_classes]

    def list(self, request, *args, **kwargs):
        out = self.fetch_data(request, self.resource_type, *args, **kwargs)
        return Response(out)

    def retrieve(self, request, resource_id=None, *args, **kwargs):
        out = self.fetch_data(request, self.resource_type, resource_id=resource_id, *args, **kwargs)
        return Response(out)

    # A lot of this is copied (haphazardly) from generic, and the names and handling of the schema could be cleaned up
    def get_query_schema(self):
        if getattr(self, 'action', None) == 'list':
            return getattr(self, 'SEARCH_QUERY_SCHEMA', getattr(self, 'QUERY_SCHEMA', {}))
        return {}

    def get_query_transforms(self):
        if getattr(self, 'action', None) == 'list':
            return getattr(self, 'SEARCH_QUERY_TRANSFORMS', getattr(self, 'QUERY_TRANSFORMS', {}))
        return getattr(self, 'QUERY_TRANSFORMS', {})

    def map_parameters(self, params):
        transforms = self.get_query_transforms()
        for key, correct in transforms.items():
            val = params.pop(key, None)
            if val is not None:
                params[correct] = val
        return params

    def filter_parameters(self, request):
        if getattr(self, 'action', None) != 'list':
            return {}

        params = self.map_parameters(request.query_params.dict())
        params['_lastUpdated'] = request.query_params.getlist('_lastUpdated')

        schema = Schema(self.get_query_schema(), extra=REMOVE_EXTRA)
        return schema(params)

    # TODO - investigate if this is needed, or if we can assume application/json+fhir everywhere
    def build_parameters(self, request):
        return {'_format': 'application/json+fhir'}
