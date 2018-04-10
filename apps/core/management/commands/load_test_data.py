import json

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand

from apps.capabilities.models import ProtectedCapability
from apps.dot_ext import Application


class Command(BaseCommand):
    help = 'Load Test Data for hhs_oauth_server'

    def handle(self, *args, **options):
        # create application.read group and application.write group
        try:
            read_group = Group.objects.get(name='application.test_read')
            self._log('read group exists')
        except Group.DoesNotExist:
            read_group = Group.objects.create(name='application.test_read')
            self._log('read group created')

        try:
            write_group = Group.objects.get(name='application.test_write')
            self._log('write groups exist')
        except Group.DoesNotExist:
            write_group = Group.objects.create(name='application.test_write')
            self._log('write groups created')

        # create test_dev user and add to both groups
        try:
            test_dev = User.objects.get(username='test_dev')
            self._log('test_user dev exist')
        except User.DoesNotExist:
            test_dev = User.objects.create_user('test_dev', password='foobarbaz')
            self._log('test_dev user created and added to read and write groups')
        finally:
            test_dev.groups.add(read_group)
            test_dev.groups.add(write_group)

        # create test_user
        try:
            User.objects.get(username='test_user')
            self._log('test_user user exist')
        except User.DoesNotExist:
            User.objects.create_user(
                'test_user', password='foobarbaz', first_name='Test',
                last_name='User', email='test_user@a.com')
            self._log('test_user user created')

        # create read capability
        try:
            read_capability = ProtectedCapability.objects.get(slug='read-capability')
        except ProtectedCapability.DoesNotExist:
            read_urls = [['GET', '/api/read/']]
            read_capability = ProtectedCapability.objects.create(
                title='read capability', slug='read-capability',
                protected_resources=json.dumps(read_urls), group=read_group)
            self._log('read capability created')

        # create write capability
        try:
            write_capability = ProtectedCapability.objects.get(slug='write-capability')
        except ProtectedCapability.DoesNotExist:
            write_urls = [['POST', '/api/write/']]
            write_capability = ProtectedCapability.objects.create(
                title='write capability', slug='write-capability',
                protected_resources=json.dumps(write_urls), group=write_group)
            self._log('write capability created')

        # create an application with read capability
        try:
            read_application = Application.objects.get(name='test-app-read')
            self._log('read application exist')
        except Application.DoesNotExist:
            read_application = Application.objects.create(
                name='test-app-read', user=test_dev,
                client_type=Application.CLIENT_PUBLIC,
                authorization_grant_type=Application.GRANT_PASSWORD,
                client_id='test_app_read', client_secret='test_app_read')
            read_application.scope.add(read_capability)
            self._log('read application created')

        # create an application with write capability
        try:
            write_application = Application.objects.get(name='test-app-write')
            self._log('write application exist')
        except Application.DoesNotExist:
            write_application = Application.objects.create(
                name='test-app-write', user=test_dev,
                client_type=Application.CLIENT_PUBLIC,
                authorization_grant_type=Application.GRANT_PASSWORD,
                client_id='test_app_write', client_secret='test_app_write')
            write_application.scope.add(write_capability)
            self._log('write application created')

        # create a base test app used for social login testing
        try:
            Application.objects.get(name='test-app')
            self._log('base application exist')
        except Application.DoesNotExist:
            Application.objects.create(
                name='test-app', user=test_dev,
                client_type=Application.CLIENT_PUBLIC,
                authorization_grant_type=Application.GRANT_PASSWORD,
                client_id='test_app', client_secret='test_app')
            self._log('base application created')

    def _log(self, message):
        self.stdout.write(message)
