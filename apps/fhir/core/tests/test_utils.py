from django.test import TestCase

from apps.fhir.bluebutton.utils import check_access_interaction_and_resource_type
from apps.fhir.server.models import SupportedResourceType


class Utils_TestCase(TestCase):
    """
    Test FHIR Create
    """

    def test_check_access_interaction_and_resource_type_valid(self):
        """
        Tests that SupportedResourceType returns valid result = False
            resource_name      = 'Patient',
            json_schema        = '{}',
            get                = True,
            put                = True,
            create             = True,
            read               = True,
            vread              = False,
            update             = False,
            delete             = False,
            search             = False,
            history            = False,
        """

        SupportedResourceType.objects.create(
            resource_name='Patient',
            json_schema='{}',
            get=True,
            put=True,
            create=True,
            read=True,
            vread=False,
            update=False,
            delete=False,
            search=False,
            history=False,
        )

        resource_type = 'Patient'
        interaction_type = 'read'
        response = check_access_interaction_and_resource_type(resource_type, interaction_type)
        self.assertEqual(response, False)

    def test_check_access_interaction_and_resource_type_no_resource(self):
        """
        Tests no SupportedResourceType found returns 404
        """
        SupportedResourceType.objects.create(
            resource_name='Patient',
            json_schema='{}',
            get=True,
            put=True,
            create=True,
            read=True,
            vread=False,
            update=False,
            delete=False,
            search=False,
            history=False,
        )

        resource_type = 'Practitioner'
        interaction_type = 'read'
        response = check_access_interaction_and_resource_type(resource_type, interaction_type)
        self.assertEqual(response.status_code, 404)

    def test_check_access_interaction_and_resource_type_no_interaction(self):
        """
        Tests no SupportedResourceType interaction_type found returns 403
        """
        SupportedResourceType.objects.create(
            resource_name='Patient',
            json_schema='{}',
            get=True,
            put=True,
            create=True,
            read=True,
            vread=False,
            update=False,
            delete=False,
            search=False,
            history=False,
        )

        resource_type = 'Patient'
        interaction_type = 'vread'
        response = check_access_interaction_and_resource_type(resource_type, interaction_type)
        self.assertEqual(response.status_code, 403)
