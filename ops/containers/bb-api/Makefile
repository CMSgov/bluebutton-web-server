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
		-t bb-api:latest \
		-f Dockerfile \
		../../..

build-codebuild:
	echo "build-codebuild"
	TARGET_ENV="test"
	docker build \
		--build-arg RELEASE_TAG="local" \
		--build-arg BUILD_TARGET="codebuild" \
		-t bb-api:latest \
		-f Dockerfile \
		../../..

run-codebuild:
	echo "run-cicd"
	bfd="test" \
	env=${env} \
	auth="live" \
	TARGET_ENV="test" \
	./scripts/external/prepare-environment.bash

build-local-no-cache:
	echo "build-local no-cache"
	TARGET_ENV="local" \
	docker build \
		--build-arg RELEASE_TAG="local" \
		--build-arg BUILD_TARGET="local" \
		--no-cache \
		-t bb-api:latest \
		-f Dockerfile \
		../../..

run-local:
	bfd=${bfd} \
	env=${env} \
	auth=${auth} \
	TARGET_ENV="local" \
	./scripts/external/prepare-environment.bash
