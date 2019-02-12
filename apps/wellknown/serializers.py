from rest_framework.serializers import (ModelSerializer, SerializerMethodField)
from ..dot_ext.models import Application, ApplicationLabel


class ApplicationLabelSerializer(ModelSerializer):
    class Meta:
        model = ApplicationLabel
        fields = (
            'name',
            'slug',
            'description',
        )


class ApplicationListSerializer(ModelSerializer):
    labels = SerializerMethodField()

    class Meta:
        model = Application
        fields = ('name', 'website_uri', 'logo_uri', 'tos_uri', 'policy_uri',
                  'support_email', 'support_phone_number', 'description', 'labels')

    def get_labels(self, obj):
        labels = ApplicationLabel.objects.filter(applications=obj.id).values('name', 'slug', 'description')
        return(labels)
