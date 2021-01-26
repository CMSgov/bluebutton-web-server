#!/bin/sh
#
# This script runs the integration tests.
#
# This is called by docker-compose/run_integration_tests_inside_cbc_build_docker.sh
# script for CBC and local development scripts.

python runtests.py --integration apps.integration_tests.integration_test_fhir_resources.IntegrationTestFhirApiResources
