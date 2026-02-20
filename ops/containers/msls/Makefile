all: build-local

build-local:
	docker build \
    	--platform "linux/amd64" \
    	-t msls:latest \
    	-f Dockerfile .

build-cloud:
	echo "Mock SLSX does not get built for the cloud."