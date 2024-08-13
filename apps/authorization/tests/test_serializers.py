from apps.test import BaseApiTest
from ..views import ApplicationSerializer


class TestApplicationSerializer(BaseApiTest):

    def test_application_serializer(self):
        dev_user = self._create_user("developer_test", "123456")
        test_app = self._create_application(
            "test_app",
            user=dev_user,
            logo_uri="example.com/logo",
            tos_uri="example.com/tos",
            policy_uri="example.com/policy",
            contacts="contacts@example.com",
            support_email="support@example.com",
        )

        serializer = ApplicationSerializer(test_app)
        serialized = serializer.data
        print(serializer.data)
        expected = {
            'id': 1,
            'name': 'test_app',
            'logo_uri': 'example.com/logo',
            'tos_uri': 'example.com/tos',
            'policy_uri': 'example.com/policy',
            'contacts': 'support@example.com'
        }

        self.assertEqual(serialized, expected)
