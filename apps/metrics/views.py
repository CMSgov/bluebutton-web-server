from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from ..accounts.models import UserProfile


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
            'beneficiary_count': UserProfile.objects.filter(user_type='BEN').count()
        }
        return Response(content)
