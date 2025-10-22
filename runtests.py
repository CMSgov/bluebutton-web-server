#!/usr/bin/env python
import argparse
import django
import os
import sys
from datetime import datetime
from io import StringIO

from django.conf import settings
from django.test.utils import get_runner

'''
    Reference: https://docs.djangoproject.com/en/3.0/topics/testing/advanced/#defining-a-test-runner

    Command line arguments:

        --integration  This optional flag indicates tests are to run in integration test mode.
        Space separated list of Django tests to run.

        --selenium  This optional flag indicates tests are to run in selenium test mode.
        Space separated list of Django tests to run.

        --report-file This optional file name indicates that tests should be written to a file of
        this name

    For example:

        $ docker compose exec web python runtests.py apps.dot_ext.tests

        For more specific use:

        $ docker compose exec web python runtests.py apps.dot_ext.tests.test_templates

        For a single test:
        $ docker compose exec web python runtests.py apps.dot_ext.tests.\
          test_templates.TestDOTTemplates.test_application_list_template_override

        For multiple arguments:

        $ docker compose exec web python runtests.py apps.dot_ext.tests apps.accounts.tests.test_login
'''

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--integration', help='Integration tests mode', action='store_true')
parser.add_argument('--selenium', help='Selenium tests mode', action='store_true')
parser.add_argument('--report-file', help='Output test failures/errors to report file')
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
elif not args.selenium:
    # Unset ENV variables for Django unit type tests so default values get set.
    # 20251022 Removed 'FHIR_URL' from the list of env vars that are deleted.
    for env_var in ['DJANGO_MEDICARE_SLSX_LOGIN_URI', 'DJANGO_MEDICARE_SLSX_REDIRECT_URI',
                    'DJANGO_SLSX_USERINFO_ENDPOINT', 'DJANGO_SLSX_TOKEN_ENDPOINT',
                    'DJANGO_SLSX_HEALTH_CHECK_ENDPOINT', "DJANGO_SLSX_SIGNOUT_ENDPOINT",
                    'DJANGO_FHIR_CERTSTORE', 'DATABASES_CUSTOM', 'DJANGO_LOG_JSON_FORMAT_PRETTY',
                    'DJANGO_USER_ID_ITERATIONS', 'DJANGO_USER_ID_SALT']:
        if env_var in os.environ:
            del os.environ[env_var]

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'hhs_oauth_server.settings.test'
    django.setup()
    TestRunner = get_runner(settings)

    # Only capture output if report_file is specified and test flag is set
    if args.report_file and args.test:
        captured_output = StringIO()
        sys.stderr = captured_output
    else:
        captured_output = None

    test_runner = TestRunner(verbosity=2)
    if args.test:
        failures = test_runner.run_tests(args.test)
    else:
        failures = test_runner.run_tests(None)

    if captured_output and failures and args.report_file and args.test:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(args.report_file, 'w') as report:
            report.write(f"Test Report Generated: {timestamp}\n")
            report.write("=" * 60 + "\n\n")

            if args.integration:
                report.write("Mode: Integration\n")
            elif args.selenium:
                report.write("Mode: Selenium\n")
            else:
                report.write("Mode: Unit\n")

            report.write(f"Tests run: {' '.join(args.test)}\n\n")

            report.write(f"Failures/Errors: {failures}\n\n")
            report.write("=" * 60 + "\n")
            report.write("DETAILED OUTPUT:\n")
            report.write("=" * 60 + "\n")
            report.write(captured_output.getvalue())

        print(f"Test report written to: {args.report_file}")

    if failures > 0 and 'JENKINS_URL' in os.environ:
        sys.exit(1)
