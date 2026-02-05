build:
	@echo Building container to compile the requirements
	docker build \
		--platform "linux/amd64" \
		-t bb-requirements:latest \
		-f Dockerfile.compile-requirements . 

generate: clean build
	docker run \
		--platform "linux/amd64" \
		-v ./generate.bash:/requirements/generate.bash \
		-v ../vendor:/vendor \
		-v .:/output \
		-t bb-requirements:latest
		

clean:
	@echo Removing old requirements files
	rm -f requirements.dev.txt requirements.txt