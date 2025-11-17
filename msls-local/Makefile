all: build-local

build-local:
	cd msls-local ; docker build \
    	--platform "linux/amd64" \
    	-t msls-local:latest \
    	-f Dockerfile.msls .