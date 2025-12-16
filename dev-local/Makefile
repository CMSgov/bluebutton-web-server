all: build-local run-local

build-local:
	@echo "building mock sls image"
	cd ../msls-local ; make all ; cd ../dev-local
	@echo "building local blue button image"
	cd ../dev-local ; docker build \
    	--platform "linux/amd64" \
    	-t bb-local:latest \
    	-f Dockerfile.local ..
	@echo "buildilng selenium image"
	cd ../dev-local/selenium && make all

run-local:
	@echo "Configuring for ${ENV}" ; \
		./run-appropriate-stack.bash

exec-web:
	docker exec -it `docker ps -aqf "name=.*web.*"` /bin/bash

selenium-local:
	@echo "Running Selenium: Local"
	cd selenium && make all && make run-local auth=$(AUTH)