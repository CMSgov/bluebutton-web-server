build-local:
	@echo Building container to compile the requirements
	docker build \
		--platform "linux/amd64" \
		-t bb-requirements:latest \
		-f Dockerfile ../../..

run-local: clean build-local
	docker run \
		--platform "linux/amd64" \
		-v ../../../requirements:/output \
		-t bb-requirements:latest
	
clean:
	@echo Removing old requirements files
	cd ../../../requirements ; rm -f requirements.dev.txt requirements.txt