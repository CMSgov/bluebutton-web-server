build-local:
	@echo Building container to compile the requirements
	docker build \
		--platform "linux/arm64" \
		-t bb-requirements:latest \
		-f Dockerfile ../../..

run-local:
	docker run \
		--platform "linux/arm64" \
		-v ./scripts/internal/entrypoint.bash:/code/ops/containers/requirements-generation/scripts/internal/entrypoint.bash \
		-v ../../../requirements:/output \
		-t bb-requirements:latest
	
clean:
	@echo Removing old requirements files
	cd ../../../requirements ; rm -f requirements.dev.txt requirements.txt