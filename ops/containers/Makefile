SHELL:=/bin/bash
RELEASE_TAG?=TAG_NOT_SET
bfd ?= "test"
env ?= "local"
auth ?= "live"

css:
	cd bb-css ; make build-local
	cd bb-css ; make run-local

requirements:
	cd bb-requirements ; make clean
	cd bb-requirements ; make build-local
	cd bb-requirements ; make run-local

build-local: css requirements
	cd mslsx ; make build-local
	cd bb-api ; make build-local

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
	-f bb-api/Dockerfile \
	.

run-local:
	bfd="${bfd}" \
	env="${env}" \
	auth="${auth}" \
	TARGET_ENV="local" \
	bash ./bb-api/scripts/external/prepare-environment.bash

migrate:
	MIGRATE=1 \
	bfd="test" \
	env="local" \
	TARGET_ENV="local" \
	bash ./bb-api/scripts/external/prepare-environment.bash

collectstatic:
	COLLECTSTATIC=1 \
	bfd="test" \
	env="local" \
	TARGET_ENV="local" \
	bash ./bb-api/scripts/external/prepare-environment.bash

.PHONY: build-css
build-css:
	cd bb-css ; make build-css