all: build-local run-local

build-local:
	@echo "building mock sls image"
	cd ../msls-local ; make all ; cd ../dev-local
	@echo "building local blue button image"
	cd ../dev-local ; docker build \
    	--platform "linux/amd64" \
    	-t bb-local:latest \
    	-f Dockerfile.local ..
	@echo "building selenium image"
	cd ../dev-local/selenium && make all
	@echo "building the CSS builder"
	cd ../dev-local ; docker build \
		-t bbcss:latest \
		-f Dockerfile.build-css ..
	if test ! -d  ../static/bluebutton-css/dist; then \
		echo "building CSS static assets for local dev"; \
		make build-css; \
	fi

build-css:
	docker run \
		-v ./build-css.bash:/code/dev-local/build-css.bash \
		-v ../static/bluebutton-css/dist:/code/static/bluebutton-css/dist \
		bbcss:latest

run-local:
	@echo "Configuring for ${ENV}" ; \
		./run-appropriate-stack.bash

retrieve-certs:
	@echo "Retrieiving certs for $(if $(env),$(env),test)" ; \
		./scripts/retrieve-aws-certs.bash

exec-web:
	docker exec -it `docker ps -aqf "name=.*web.*"` /bin/bash

run-selenium:
	@echo "Running Selenium: Local"
	cd selenium && make run-local

build-selenium:
	@echo "Running Selenium: Local"
	cd selenium && make build-local