all: build-local run-local

build-local:
	@echo "building mock sls image"
	cd ../msls-local ; make all ; cd ../dev-local
	@echo "building local blue button image"
	cd ../dev-local ; docker build \
    	--platform "linux/amd64" \
    	-t bb-local:latest \
    	-f Dockerfile.local ..
	cd ../dev-local ; docker build \
    	--platform "linux/amd64" \
    	-t selenium-local:latest \
    	-f Dockerfile.selenium-local ..
		
run-local:
	@echo "Configuring for ${ENV}" ; \
		./run-appropriate-stack.bash
	