.PHONY: build-local run-local

build-local:
	docker build \
		-t bb-css:latest \
		-f Dockerfile ../../..

run-local:
	docker run \
		-v "$(CURDIR)/scripts/internal/build-css.bash:/code/build-css.bash" \
		bb-css:latest