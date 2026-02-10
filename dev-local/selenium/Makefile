# This is a helper Makefile, do not run from the selenium directory, compose context is relative and so it
# expects to be run from dev-local

all: build-local

build-local:
	@echo "Building Selenium Image"
	docker build \
		--platform "linux/amd64" \
		-t selenium-local:latest \
		-f Dockerfile.selenium .

run-local:
	./run-selenium-local.sh auth=$(auth) debug=$(if $(debug),$(debug),false)

run-remote:
	@echo "Running Selenium: Remote"
	@echo "TODO:"