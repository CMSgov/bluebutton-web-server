from django.conf import settings
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework import serializers
from apps.dot_ext.models import Application


class ProviderPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'publisher': {
                "organization": settings.ORGANIZATION["NAME"],
                "endpoints": {
                    "name": "metadata",
                    "address": lazy_reverse("metadata"),
                },
                "contacts": [
                    {
                        "system": "email",
                        "value": settings.ORGANIZATION["EMAIL"],
                    },
                ],
            },
            'results': data,
        })
        

class ApplicationListSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    description = serializers.CharField()
    website_uri = serializers.URLField()
    tos_uri = serializers.URLField()
    privacy_policy_uri = serializers.URLField(source="policy_uri")
    contacts = serializers.SerializerMethodField()
    
    class Meta:
        model = Application

    def get_contacts(self, obj):
        contacts = [
            {
                "system": "phone",
                "value": obj.support_phone_number
            },
            {
                "system": "email",
                "value": obj.support_email
            }
        ]




class ApplicationListView(ListAPIView):
    """
    View to provide an applications list.

    An application that has active=False or with a label slug in the APP_LIST_EXCLUDE
    list will be excluded from this view.
    """
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer,)
    serializer_class = ApplicationListSerializer
    pagination_class = ProviderPagination

    def get_queryset(self):
        queryset = Application.objects.exclude(active=False).exclude(
            applicationlabel__slug__in=settings.APP_LIST_EXCLUDE).order_by('name')
        return queryset

