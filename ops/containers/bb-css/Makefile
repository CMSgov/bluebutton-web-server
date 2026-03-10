build-local:
	docker build \
		-t bb-css:latest \
		-f Dockerfile ../../..
run-local:
	docker run \
		-v ./scripts/internal/build-css.bash:/code/build-css.bash \
		bb-css:latest