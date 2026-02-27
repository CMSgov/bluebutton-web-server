SHELL:=/bin/bash
RELEASE_TAG?=TAG_NOT_SET
bfd ?= "test"
env ?= "local"
auth ?= "live"

css:
	cd build-css ; make build-local
	cd build-css ; make run-local

requirements:
	cd requirements-generation ; make clean
	cd requirements-generation ; make build-local
	cd requirements-generation ; make run-local

build-local: css requirements
	cd msls ; make build-local
	cd bb-web-api ; make build-local

# This is speculative; not yet tested in production.
build-production:
	echo "build"
	env="local" \
	bfd=${bfd} \
	docker build \
	--platform "linux/amd64" \
	--build-arg RELEASE_TAG="${RELEASE_TAG}" \
	--build-arg BUILD_TARGET="production" \
	--no-cache \
	-t bb:latest \
	-f bb-web-api/Dockerfile \
	.

run-local:
	bfd="test" \
	env="local" \
	TARGET_ENV="local" \
	bash ./bb-web-api/scripts/external/prepare-environment.bash

migrate:
	MIGRATE=1 \
	bfd="test" \
	env="local" \
	TARGET_ENV="local" \
	bash ./bb-web-api/scripts/external/prepare-environment.bash

collectstatic:
	COLLECTSTATIC=1 \
	bfd="test" \
	env="local" \
	TARGET_ENV="local" \
	bash ./bb-web-api/scripts/external/prepare-environment.bash

.PHONY: build-css
build-css:
	cd build-css ; make build-css