# This is a helper Makefile, do not run from the selenium directory, compose context is relative and so it
# expects to be run from dev-local

AUTH  ?= live
DEBUG ?= false

run-selenium-target-local:
	auth=$(AUTH) debug=$(DEBUG) ./run-selenium-local.sh

build-selenium:
	@echo "Building Selenium Image"
	docker build \
		-t selenium-local:latest \
		-f Dockerfile.selenium .

run-remote:
	@echo "Running Selenium: Remote"
	@echo "TODO:"