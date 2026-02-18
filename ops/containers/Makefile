SHELL:=/bin/bash
RELEASE_TAG?=TAG_NOT_SET
bfd?="test"
env?="local"

# docker build --build-arg RELEASE_TAG=r178 --progress=plain -t bb:latest -f Dockerfile ../../..

# reset ; docker run -it -v ./entrypoint.bash:/bb/ops/containers/bb-web-api/entrypoint.bash -v ./nginx.conf.in:/bb/ops/containers/bb-web-api/nginx.conf.in bb:latest

build-local:
	echo "build-local"
	docker build \
		--platform "linux/amd64" \
		--build-arg RELEASE_TAG="local" \
		--build-arg BUILD_TARGET="local" \
		--no-cache \
		-t bb:latest \
		-f Dockerfile \
		../../..

build:
	echo "build"
	env="local" \
	bfd=${bfd} \
		docker build \
		--platform "linux/amd64" \
		--build-arg RELEASE_TAG="${RELEASE_TAG}" \
		--build-arg BUILD_TARGET="cloud" \
		--no-cache \
		-t bb:latest \
		-f Dockerfile \
		.

run-local:
	env="local" \
	bfd=${bfd} \
	docker run -it \
		--platform "linux/amd64" \
		-e env=${env} \
		-e bfd=${bfd} \
		-p 8000:8000 \
		-v ${PWD}:/home/boton/bb/ops/containers/bb-web-api \
		bb:latest

push:
	echo "push"