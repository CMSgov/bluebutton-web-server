SHELL       := /bin/bash
RELEASE_TAG ?= TAG_NOT_SET
bfd         ?= test
env         ?= local
auth        ?= live

.PHONY: css requirements build-local build-local-no-cache build-production run-local \
		migrate collectstatic run-selenium-target-local build-selenium

css:
	$(MAKE) -C bb-css build-local run-local

requirements:
	$(MAKE) -C bb-requirements clean build-local run-local

build-local: css requirements
	$(MAKE) -C mslsx build-local
	$(MAKE) -C bb-api build-local

build-local-no-cache:
	$(MAKE) -C bb-api build-local-no-cache

# This is speculative; not yet tested in production.
build-production:
	@echo "Building production..."
	env="local" bfd="$(bfd)" docker build \
		--platform "linux/amd64" \
		--build-arg RELEASE_TAG="$(RELEASE_TAG)" \
		--build-arg BUILD_TARGET="production" \
		--no-cache \
		-t bb:latest \
		-f bb-api/Dockerfile .

run-local:
	bfd="$(bfd)" env="$(env)" auth="$(auth)" TARGET_ENV="local" \
	bash ./bb-api/scripts/external/prepare-environment.bash

migrate:
	MIGRATE=1 bfd="test" env="local" TARGET_ENV="local" \
	bash ./bb-api/scripts/external/prepare-environment.bash

collectstatic:
	COLLECTSTATIC=1 bfd="test" env="local" TARGET_ENV="local" \
	bash ./bb-api/scripts/external/prepare-environment.bash

run-selenium-target-local:
	@echo "Running Selenium: Local"
	$(MAKE) -C selenium run-selenium-target-local AUTH="$(auth)"

build-selenium:
	@echo "Building Selenium..."
	$(MAKE) -C selenium build-selenium