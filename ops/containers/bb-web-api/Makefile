SHELL:=/bin/bash
RELEASE_TAG?=TAG_NOT_SET
bfd ?= "test"
env ?= "local"
auth ?= "live"

build-local:
	echo "build-local"
	TARGET_ENV="local" \
	docker build \
		--build-arg RELEASE_TAG="local" \
		--build-arg BUILD_TARGET="local" \
		-t bbwebapi:latest \
		-f Dockerfile \
		../../..

# FIXME: This is not yet really tested.
build-production:
	echo "build"
	env="local" \
	bfd=${bfd} \
	docker build \
	--build-arg RELEASE_TAG="${RELEASE_TAG}" \
	--build-arg BUILD_TARGET="production" \
	--no-cache \
	-t bb-web-api-prod:latest \
	-f Dockerfile \
	.

run-local:
	bfd=${bfd} \
	env=${env} \
	auth=${auth} \
	TARGET_ENV="local" \
	./scripts/external/prepare-environment.bash
