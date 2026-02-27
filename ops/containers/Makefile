SHELL:=/bin/bash
RELEASE_TAG?=TAG_NOT_SET
bfd ?= "test"
env ?= "local"
auth ?= "live"
# docker build --build-arg RELEASE_TAG=r178 --progress=plain -t bb:latest -f Dockerfile ../../..

# reset ; docker run -it -v ./entrypoint.bash:/bb/ops/containers/bb-web-api/entrypoint.bash -v ./nginx.conf.in:/bb/ops/containers/bb-web-api/nginx.conf.in bb:latest

css:
	cd build-css ; make build-local
	cd build-css ; make run-local

requirements:
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
	cd bb-web-api ; make run-local

.PHONY: build-css
build-css:
	cd build-css ; make build-css