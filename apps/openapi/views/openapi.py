import yaml
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework_yaml.renderers import YAMLRenderer


class OpenAPI(APIView):

    renderer_classes = (JSONRenderer, YAMLRenderer, )

    def get(self, request, format=None):
        with open(settings.OPENAPI_DOC, 'r') as stream:
            definition = yaml.load(stream)
        return Response(definition)
