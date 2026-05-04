# This is a helper Makefile, do not run from the selenium directory, compose context is relative and so it
# expects to be run from dev-local

auth  ?= live
debug ?= false

all: build-local

build-selenium:
	@echo "Building Selenium Image"
	docker build \
		-t selenium-local:latest \
		-f Dockerfile.selenium .

run-selenium-local:
	./run-selenium-local.sh auth=$(auth) debug=$(debug)

run-remote:
	@echo "Running Selenium: Remote"
	@echo "TODO:"