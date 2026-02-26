all: build-local

build-local:
	docker build \
    	--platform "linux/arm64" \
    	-t msls-local:latest \
    	-f Dockerfile.msls .