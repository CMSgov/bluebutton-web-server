#!/usr/bin/env python
import os
import sys
import django

from django.conf import settings
from django.test.utils import get_runner


'''
    Reference: https://docs.djangoproject.com/en/3.0/topics/testing/advanced/#defining-a-test-runner

    Command line arguments sys.argv[1:] is a list of specific tests to run.

    For example:
        $ docker-compose exec web python runtests.py apps.dot_ext.tests

        For more specific use:

        $ docker-compose exec web python runtests.py apps.dot_ext.tests.test_templates

        For a single test:
        $ docker-compose exec web python runtests.py apps.dot_ext.tests.\
          test_templates.TestDOTTemplates.test_application_list_template_override

        For multiple arguments:

        $ docker-compose exec web python runtests.py apps.dot_ext.tests apps.accounts.tests.test_login
'''

# Unset ENV variables so that tests use default values.
for env_var in ['FHIR_URL', 'DJANGO_MEDICARE_LOGIN_URI',
                'DJANGO_SLS_USERINFO_ENDPOINT', 'DJANGO_SLS_TOKEN_ENDPOINT',
                'DJANGO_FHIR_CERTSTORE', 'DATABASES_CUSTOM']:
    if env_var in os.environ:
        del os.environ[env_var]

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'hhs_oauth_server.settings.test'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    # Is there a list of specific tests to run?
    if len(sys.argv) > 1:
        failures = test_runner.run_tests(sys.argv[1:])
    else:
        failures = test_runner.run_tests(None)
    sys.exit(bool(failures))
