all: build-local run-local

build-local:
	@echo "building mock sls image"
	cd ../msls-local ; make all
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
	