from django.test import TestCase

from apps.fhir.bluebutton.utils import (check_access_interaction_and_resource_type,
                                        get_resourcerouter)

from apps.fhir.server.models import SupportedResourceType


class Utils_TestCase(TestCase):
    """
    Test FHIR Create
    """

    fixtures = ['fhir_bluebutton_test_rt.json']

    def test_check_access_interaction_and_resource_type_valid(self):
        """
        Tests that SupportedResourceType returns valid result = False
            resource_name      = 'Patient',
            fhir_source        = 1,
            resourceType       = 'Patient',
            secure_access      = true,
            json_schema        = '{}',
            get                = true,
            put                = true,
            create             = true,
            read               = true,
            vread              = true,
            update             = false,
            delete             = false,
            search             = false,
            history            = false,
            override_url_id    = true,
            override_search    = true,
            search_block       = "['Patient', 'patient', ]",
            search_add         = "patient=%PATIENT%"

        """
        rr = get_resourcerouter()

        SupportedResourceType.objects.create(
            resource_name='Person-First',
            fhir_source=rr,
            resourceType='Person',
            secure_access=True,
            json_schema='{}',
            get=True,
            put=True,
            create=True,
            read=True,
            vread=True,
            update=False,
            delete=False,
            search=False,
            history=False,
            override_url_id=True,
            override_search=True,
            search_block="['Patient', 'patient', ]",
            search_add="patient=%PATIENT%"
        )

        resource_type = 'Person'
        interaction_type = 'read'
        rr = get_resourcerouter()
        response = check_access_interaction_and_resource_type(resource_type,
                                                              interaction_type,
                                                              rr)
        self.assertEqual(response, False)

    def test_check_access_interaction_and_resource_type_no_resource(self):
        """
        Tests no SupportedResourceType found returns 404
        """
        rr = get_resourcerouter()

        SupportedResourceType.objects.create(
            resource_name='Person-other',
            fhir_source=rr,
            resourceType='Person',
            secure_access=True,
            json_schema='{}',
            get=True,
            put=True,
            create=True,
            read=True,
            vread=True,
            update=False,
            delete=False,
            search=False,
            history=False,
            override_url_id=True,
            override_search=True,
            search_block="['Patient', 'patient', ]",
            search_add="patient=%PATIENT%"
        )

        resource_type = 'Encounter'
        interaction_type = 'read'
        rr = get_resourcerouter()
        response = check_access_interaction_and_resource_type(resource_type,
                                                              interaction_type,
                                                              rr)
        self.assertEqual(response.status_code, 404)

    def test_check_access_interaction_and_resource_type_no_interaction(self):
        """
        Tests no SupportedResourceType interaction_type found returns 403
        """

        rr = get_resourcerouter()

        # print("RR:%s" % rr)

        SupportedResourceType.objects.create(
            resource_name='Person-another',
            fhir_source=rr,
            resourceType='Person',
            secure_access=True,
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
            override_url_id=True,
            override_search=True,
            search_block="['Patient', 'patient', ]",
            search_add="patient=%PATIENT%"
        )

        resource_type = 'Person'
        interaction_type = 'vread'

        response = check_access_interaction_and_resource_type(resource_type,
                                                              interaction_type,
                                                              rr)
        self.assertEqual(response.status_code, 403)
