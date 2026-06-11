ROOT_DIR    := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
SHELL       := /bin/bash
RELEASE_TAG ?= TAG_NOT_SET
bfd         ?= test
env         ?= local
auth        ?= live

.PHONY: build-local build-local-no-cache build-codebuild run-codebuild \
        run-codebuild-integration teardown-codebuild run-local

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

run-codebuild:
	@echo "Running codebuild environment"
	bfd="test" env="test" auth="live" TARGET_ENV="codebuild" \
	bash $(ROOT_DIR)/scripts/external/prepare-environment.bash

run-codebuild-integration:
	@echo "integration tests in Codebuild"
	docker compose \
		-f ../docker-compose-codebuild.yaml \
		exec -T bb-api pytest --collect-only -m 'integration' -vv --tb=short >> collectedtests.txt

teardown-codebuild:
	docker compose -f ../docker-compose-codebuild.yaml down -v

run-local:
	bfd="$(bfd)" env="$(env)" auth="$(auth)" TARGET_ENV="local" \
	bash $(ROOT_DIR)/scripts/external/prepare-environment.bash