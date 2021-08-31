#!/usr/bin/env python
import argparse
import django
import os
import sys

from django.conf import settings
from django.test.utils import get_runner

'''
    Reference: https://docs.djangoproject.com/en/3.0/topics/testing/advanced/#defining-a-test-runner

    Command line arguments:

        --integration  This optional flag indicates tests are to run in integration test mode.
        Space separated list of Django tests to run.

        --selenium  This optional flag indicates tests are to run in selenium test mode.
        Space separated list of Django tests to run.

        --logit  This optional flag indicates tests are to run in logging integration test mode.
        Space separated list of Django tests to run.

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

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--integration', help='Integration tests mode', action='store_true')
parser.add_argument('--selenium', help='Selenium tests mode', action='store_true')
parser.add_argument('--logit', help='Logging tests mode (use selenium as driver)', action='store_true')
parser.add_argument('test', nargs='*')
args = parser.parse_args()

if args.integration:
    # Unset ENV variables for integration type tests so default values get set.
    for env_var in ['DJANGO_MEDICARE_SLSX_LOGIN_URI', 'DJANGO_MEDICARE_SLSX_REDIRECT_URI',
                    'DJANGO_SLSX_USERINFO_ENDPOINT', 'DJANGO_SLSX_TOKEN_ENDPOINT',
                    'DJANGO_SLSX_HEALTH_CHECK_ENDPOINT', "DJANGO_SLSX_SIGNOUT_ENDPOINT",
                    'DATABASES_CUSTOM', 'DJANGO_LOG_JSON_FORMAT_PRETTY']:
        if env_var in os.environ:
            del os.environ[env_var]
elif not args.selenium and not args.logit:
    # For tests using selenium, inherit SLSX config from context;
    # Unset ENV variables for Django unit type tests so default values get set.
    for env_var in ['FHIR_URL', 'DJANGO_MEDICARE_SLSX_LOGIN_URI', 'DJANGO_MEDICARE_SLSX_REDIRECT_URI',
                    'DJANGO_SLSX_USERINFO_ENDPOINT', 'DJANGO_SLSX_TOKEN_ENDPOINT',
                    'DJANGO_SLSX_HEALTH_CHECK_ENDPOINT', "DJANGO_SLSX_SIGNOUT_ENDPOINT",
                    'DJANGO_FHIR_CERTSTORE', 'DATABASES_CUSTOM', 'DJANGO_LOG_JSON_FORMAT_PRETTY',
                    'DJANGO_USER_ID_ITERATIONS', 'DJANGO_USER_ID_SALT']:
        if env_var in os.environ:
            del os.environ[env_var]

if __name__ == '__main__':
    if not args.selenium and not args.logit:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'hhs_oauth_server.settings.test'
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'hhs_oauth_server.settings.dev'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    # Is there a list of specific tests to run?
    if args.test:
        failures = test_runner.run_tests(args.test)
    else:
        failures = test_runner.run_tests(None)
    sys.exit(bool(failures))
