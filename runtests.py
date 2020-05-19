#!/usr/bin/env python
import os
import sys
import django

from django.conf import settings
from django.test.utils import get_runner


# Unset ENV variables so that tests use default values.
del os.environ['FHIR_URL']
del os.environ['DJANGO_MEDICARE_LOGIN_URI']
del os.environ['DJANGO_SLS_USERINFO_ENDPOINT']
del os.environ['DJANGO_SLS_TOKEN_ENDPOINT']
del os.environ['DJANGO_FHIR_CERTSTORE']

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'hhs_oauth_server.settings.test'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(None)
    sys.exit(bool(failures))
