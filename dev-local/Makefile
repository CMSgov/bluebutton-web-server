all: build-local run-local

buildenv:
	cd ../dev-local ; docker build \
		--platform "linux/amd64" \
		-t buildenv:latest \
		-f Dockerfile.buildenv ..

run-buildenv:
	cd ../dev-local ; docker run --platform linux/amd64 -v ${PWD}/..:/code -it buildenv:latest

# --progress=plain
# if you want to see the build process in a less-fancy way.
build-local:
	@echo "building mock sls image"
	cd ../msls-local ; make all ; cd ../dev-local
	@echo "building local blue button image"
	cd ../dev-local ; docker build \
    	--platform "linux/amd64" \
    	-t bb-local:latest \
    	-f Dockerfile.local ..
# TODO: Is this necessary in a local build? Probably not.
#	@echo "building selenium ecr image"
# 	cd ../dev-local ; docker build \
#     	--platform "linux/amd64" \
#     	-t selenium-ecr:latest \
#     	-f Dockerfile.selenium-ecr ..
	cd ../dev-local ; docker build \
    	--platform "linux/amd64" \
    	-t selenium-local:latest \
    	-f Dockerfile.selenium-local ..
run-local:
	@echo "Configuring for ${ENV}" ; \
		./run-appropriate-stack.bash
	