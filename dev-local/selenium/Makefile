# This is a helper Makefile, do not run from the selenium directory, compose context is relative and so it
# expects to be run from dev-local

all: build-local

build-local:
	@echo "Building selenium image"
	cd .. && docker-compose -f docker-compose-local.yaml -f selenium/docker-compose-selenium.yaml build

run-local:
	@echo "Running Selenium: Local"
	./run-selenium-local.sh $(AUTH)

run-remote:
	@echo "Running Selenium: Remote"
	@echo "TODO:"