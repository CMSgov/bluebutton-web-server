from django.conf import settings
from django.urls import reverse_lazy
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework import serializers
from rest_framework.response import Response
from apps.dot_ext.models import Application


class ProviderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10000

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'publisher': self.get_publisher_data(),
            'results': data,
        })

    def get_publisher_data(self):
        try:
            return {
                "organization": settings.ORGANIZATION["NAME"],
                "endpoints": {
                    "name": "metadata",
                    "address": reverse_lazy("fhir_conformance_metadata"),
                },
                "contacts": [
                    {
                        "system": "email",
                        "value": settings.ORGANIZATION["EMAIL"],
                    },
                ],
            }
        except Exception:
            return {}


class ApplicationListSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    description = serializers.CharField()
    website_uri = serializers.URLField()
    tos_uri = serializers.URLField()
    privacy_policy_uri = serializers.URLField(source="policy_uri")
    contacts = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            'name',
            'description',
            'website_uri',
            'tos_uri',
            'privacy_policy_uri',
            'contacts',
        )

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
        return contacts


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
