all: build-local run-local

build-local:
	cd ../msls-local ; make all ; \
	cd ../dev-local ; \
	docker build \
    	--platform "linux/amd64" \
    	-t bb-local:latest \
    	-f Dockerfile.local .. ; \
	cd ..

# https://stackoverflow.com/questions/2826029/passing-additional-variables-from-command-line-to-make

run-local:
# Environments in Makefiles are strange. Once we source, we have to run from the same line, basically.
# Also, you have to outdent comments to make sure they aren't passed to the shell. :sigh:
	@echo "Configuring for ${ENV}" ; \
		./check-env-preconditions.bash ; \
		./retrieve-certs.bash ; \
		source retrieve-salt.bash ; \
		./check-env-postconditions.bash ; \
		./run-appropriate-stack.bash
	