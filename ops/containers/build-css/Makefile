build-local:
	docker build \
		-t bbcss:latest \
		-f Dockerfile ../../..
	docker run \
		-v ./scripts/internal/build-css.bash:/code/dev-local/build-css.bash \
		-v ../../../static/bluebutton-css/dist:/code/static/bluebutton-css/dist \
		bbcss:latest