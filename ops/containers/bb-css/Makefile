.PHONY: build-local run-local

build-local:
	docker build \
		-t bb-css:latest \
		--load \
		-f Dockerfile ../../..

run-local:
	docker run \
		-v "$(CURDIR)/scripts/internal/build-css.bash:/code/build-css.bash:ro" \
        -v "$(CURDIR)/../../../static/bluebutton-css/dist:/code/static/bluebutton-css/dist" \
		bb-css:latest
