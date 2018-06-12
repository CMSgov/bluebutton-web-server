from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from ..accounts.models import UserProfile
from ..dot_ext.models import Application
from oauth2_provider.models import AccessToken


class BeneMetricsView(APIView):
    """
    View to provide beneficiary metrics.

    * Only admin users are able to access this view.
    * Default returns count info
    """
    permission_classes = (
        IsAuthenticated,
        IsAdminUser,
    )

    renderer_classes = (JSONRenderer, )

    def get(self, request, format=None):
        content = {
            'count': UserProfile.objects.filter(user_type='BEN').count()
        }
        return Response(content)


class AppMetricsView(APIView):
    """
    View to provide application metrics.

    * Only admin users are able to access this view.
    * Default returns count info
    """
    permission_classes = (
        IsAuthenticated,
        IsAdminUser,
    )

    renderer_classes = (JSONRenderer, )

    def get(self, request, format=None):
        content = {
            'count': Application.objects.count()
        }
        return Response(content)


class TokenMetricsView(APIView):
    """
    View to provide access token metrics.

    * Only admin users are able to access this view.
    * Default returns count info
    """
    permission_classes = (
        IsAuthenticated,
        IsAdminUser,
    )

    renderer_classes = (JSONRenderer, )

    def get(self, request, format=None):
        content = {
            'count': AccessToken.objects.count()
        }
        return Response(content)
