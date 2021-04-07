from django.contrib.auth.models import User
from oauth2_provider.models import get_application_model

from apps.dot_ext.models import get_application_counts
from apps.test import BaseApiTest


class TestDotExtModels(BaseApiTest):
    def test_get_application_active_counts(self):
        '''
        Test the get_application_active_counts() function
        from apps.dot_ext.models
        '''
        Application = get_application_model()

        redirect_uri = 'http://localhost'

        # create capabilities
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])

        # Create 5x active applications.
        dev_user = User.objects.create_user('dev', password='123456')
        for cnt in range(5):
            app = self._create_application('application_' + str(cnt),
                                           grant_type=Application.GRANT_AUTHORIZATION_CODE,
                                           user=dev_user,
                                           redirect_uris=redirect_uri)
            app.scope.add(capability_a, capability_b)

        # Create 3x in-active applications.
        dev_user = User.objects.create_user('dev2', password='123456')
        for cnt in range(3):
            app = self._create_application('application_' + str(cnt),
                                           grant_type=Application.GRANT_AUTHORIZATION_CODE,
                                           user=dev_user,
                                           redirect_uris=redirect_uri)
            app.scope.add(capability_a, capability_b)
            app.active = False
            app.save()

        # Assert app counts
        self.assertEqual("{'active_cnt': 5, 'inactive_cnt': 3}", str(get_application_counts()))
