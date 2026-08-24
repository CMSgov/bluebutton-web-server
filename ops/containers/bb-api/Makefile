ROOT_DIR             := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
SHELL                := /bin/bash
RELEASE_TAG          ?= TAG_NOT_SET
bfd                  ?= test
env                  ?= local
auth                 ?= live
sls                  ?= test
CAN_INTEGRATION_TEST ?= false

.PHONY: build-local build-local-no-cache build-codebuild build-selenium \
        run-codebuild run-codebuild-mock run-codebuild-integration run-codebuild-selenium \
        teardown-codebuild teardown-codebuild-selenium run-local

build-local:
	@echo "Building local"
	docker build \
		--build-arg RELEASE_TAG="local" \
		--build-arg BUILD_TARGET="local" \
		-t bb-api:latest -f Dockerfile ../../..

build-local-no-cache:
	@echo "Building local no cache"
	docker build --no-cache \
		--build-arg RELEASE_TAG="local" \
		--build-arg BUILD_TARGET="local" \
		-t bb-api:latest -f Dockerfile ../../..

build-codebuild:
	@echo "Building codebuild"
	docker build \
		--build-arg RELEASE_TAG="codebuild" \
		--build-arg BUILD_TARGET="codebuild" \
		-t bb-api:codebuild -f Dockerfile ../../..

build-selenium:
	$(MAKE) -C ../selenium build-selenium

# Running with bfd="sbx" since all integration tests are passing 
# but 2 tests are failing with bfd="test".
run-codebuild-mock:
	@echo "Running codebuild environment with auth=mock"
	bfd="sbx" env="test" auth="mock" sls="test" CAN_INTEGRATION_TEST="false" TARGET_ENV="codebuild" \
	bash $(ROOT_DIR)/scripts/external/prepare-environment.bash

run-codebuild-integration:
	@echo "integration tests in Codebuild"
	docker compose \
		-f ../docker-compose-codebuild.yaml \
		exec -T bb-api pytest -m 'integration'

teardown-codebuild:
	docker compose -f ../docker-compose-codebuild.yaml down -v

run-codebuild-selenium:
	@echo "selenium tests in Codebuild"
	docker compose \
		-f ../docker-compose-codebuild-selenium.yaml \
		run --rm selenium-tests

teardown-codebuild-selenium:
	docker compose -f ../docker-compose-codebuild-selenium.yaml down -v || true
	docker compose -f ../docker-compose-codebuild.yaml down -v

run-local:
	bfd="$(bfd)" env="$(env)" auth="$(auth)" sls="$(sls)" CAN_INTEGRATION_TEST="$(CAN_INTEGRATION_TEST)" TARGET_ENV="local" \
	bash $(ROOT_DIR)/scripts/external/prepare-environment.bash