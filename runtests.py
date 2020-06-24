#!/usr/bin/env python
import os
import sys
import django

from django.conf import settings
from django.test.utils import get_runner


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
    failures = test_runner.run_tests(None)
    sys.exit(bool(failures))
