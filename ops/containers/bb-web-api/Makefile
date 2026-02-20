SHELL:=/bin/bash
RELEASE_TAG?=TAG_NOT_SET
bfd ?= "test"
env ?= "local"
auth ?= "live"
# docker build --build-arg RELEASE_TAG=r178 --progress=plain -t bb:latest -f Dockerfile ../../..

# reset ; docker run -it -v ./entrypoint.bash:/bb/ops/containers/bb-web-api/entrypoint.bash -v ./nginx.conf.in:/bb/ops/containers/bb-web-api/nginx.conf.in bb:latest

build-local:
	echo "build-local"
	docker build \
		--platform "linux/amd64" \
		--build-arg RELEASE_TAG="local" \
		--build-arg BUILD_TARGET="local" \
		-t bb:latest \
		-f Dockerfile \
		../../..

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
		-f Dockerfile \
		.

run-local:
	bfd=${bfd} \
	env=${env} \
	auth=${auth} \
	./scripts/external/prepare-environment.bash