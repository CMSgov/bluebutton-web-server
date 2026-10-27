.PHONY: build-local run-local clean

build-local:
	@echo "Building container to compile the requirements"
	docker build \
		-t bb-requirements:latest \
		-f Dockerfile ../../..

run-local:
	docker run \
		-v "$(CURDIR)/scripts/internal/entrypoint.bash:/code/ops/containers/bb-requirements/scripts/internal/entrypoint.bash" \
		-v "$(CURDIR)/../../../requirements:/output" \
		-t bb-requirements:latest

clean:
	@echo "Removing old requirements files"
	rm -f ../../../requirements/requirements.txt ../../../requirements/requirements.dev.txt