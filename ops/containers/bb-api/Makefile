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
	docker compose -f ../docker-compose-codebuild.yaml exec -T bb-api sh -c '\
	  mkdir -p "$$DJANGO_FHIR_CERTSTORE" && \
	  printf "%s" "$$BFD_CERT_PEM_B64" | base64 -d > "$$DJANGO_FHIR_CERTSTORE/ca.cert.pem" && \
	  printf "%s" "$$BFD_KEY_PEM_B64"  | base64 -d > "$$DJANGO_FHIR_CERTSTORE/ca.key.nocrypt.pem"'
	docker compose -f ../docker-compose-codebuild.yaml exec -T bb-api sh -c \
	  'echo "CERTSTORE=[$$DJANGO_FHIR_CERTSTORE]"; ls -la /tmp/certstore/ 2>&1; \
	   wc -c /tmp/certstore/ca.cert.pem /tmp/certstore/ca.key.nocrypt.pem 2>&1'
	docker compose \
		-f ../docker-compose-codebuild.yaml \
		exec -T -e LOCAL_TESTING_TARGET=impl bb-api pytest -m 'integration' -x -vv --tb=short

teardown-codebuild:
	docker compose -f ../docker-compose-codebuild.yaml down -v

run-local:
	bfd="$(bfd)" env="$(env)" auth="$(auth)" TARGET_ENV="local" \
	bash $(ROOT_DIR)/scripts/external/prepare-environment.bash