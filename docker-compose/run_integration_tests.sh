#!/bin/sh
#
# This script runs the integration tests.
#
#     Add any new integration test files to the runtests.py list here. 

python runtests.py --integration apps.integration_tests.integration_test_fhir_resources.IntegrationTestFhirApiResources
