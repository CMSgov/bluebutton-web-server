#!/bin/sh
#
# This script runs the integration tests.
#
# This is called by the CB Core project and local dev scripts.

python runtests.py --integration apps.integration_tests.integration_test_fhir_resources.IntegrationTestFhirApiResources

result_status=$?
echo
echo RESULT_STATUS:  ${result_status}
echo
exit ${result_status}
