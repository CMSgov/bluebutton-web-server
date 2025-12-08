build:
	docker build -t bb-requirements:latest -f Dockerfile.compile-requirements . 
generate:
	docker run \
		-v ./generate.bash:/requirements/generate.bash \
		-v .:/output -t bb-requirements:latest 