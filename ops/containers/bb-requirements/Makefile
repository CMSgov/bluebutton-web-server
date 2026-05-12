build-local:
	@echo Building container to compile the requirements
	docker build \
		-t bb-requirements:latest \
		-f Dockerfile ../../..

run-local:
	docker run \
		-v ./scripts/internal/entrypoint.bash:/code/ops/containers/bb-requirements/scripts/internal/entrypoint.bash \
		-v ../../../requirements:/output \
		-t bb-requirements:latest
	
clean:
	@echo Removing old requirements files
	cd ../../../requirements ; rm -f requirements.dev.txt requirements.txt