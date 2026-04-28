build-local:
	cd ops/containers ; make build-local ; cd ../..

run-local:
	cd ops/containers ; make run-local ; cd ../..

exec-web:
	cd ops/containers ; make exec-web ; cd ../..

run-selenium:
	cd ops/containers ; make run-selenium ; cd ../..

reqs-install:
	pip install -r requirements/requirements.txt

reqs-install-dev:
	pip install -r requirements/requirements.dev.txt

generate generate-requirements:
	cd ops/containers ; make requirements ; cd ../..

generate-dev generate-reqs-dev:
	cd ops/containers ; make requirements-dev ; cd ../..

retrieve-certs:
	cd ops/containers ; make retrieve-certs ; cd ../..

migrate:
	cd ops/containers ;  make migrate ; cd ../..

collectstatic:
	cd ops/containers ; make collectstatic ; cd ../..