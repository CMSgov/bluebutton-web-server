# Docker Compose

## BFD
The bfd system needs a few variables to be set:
- `BFD_DIR` specifies the directory on your host machine where you have cloned https://github.com/CMSgov/beneficiary-fhir-data
- (optional) `SYNTHETIC_DATA` specifies a folder where you have the full set of synthetic rif files.
- (defaults to `/app`) `BFD_MOUNT_POINT` the path within the service container where the beneficiary-fhir-data directory will be mounted.

Here's an example `.env` file that docker-compose could use:

```
BFD_DIR=../../beneficiary-fhir-data
BB20_CONTEXT=../../bb2_dev_local_B
SYNTHETIC_DATA=./synthetic-data
CERTSTORE=./certstore
BB20_ENABLE_REMOTE_DEBUG=true

```
the .env assume a source tree topology as below:
<cms_projects_base_dir>/bluebutton-web-server
<cms_projects_base_dir>/beneficiary-fhir-data

run following commands to build container and start up instances:

```
docker-compose up -d bfd
docker-compose logs -f | grep bfd_1
docker-compose exec bfd make load
```
then build and start up down stream blue button server:

## bb 2.0 specific
```
docker-compose up -d bb20
docker-compose logs -f | grep bb20
docker-compose exec bb20 ./docker-compose/migrate.sh
```

## To work on Windows, a linux sub system is required:
## Tetsted with Cygwin, WSL, VirtualBox + Linux
## For Docker server, please install Docker Desktop on host (Windows)
## and set DOCKER_HOST environment variable in linux sub system
## On Windows, take care of EOL CRLF/LF by 

```
git config --global core.autocrlf true
```
and in .env add below hint:
COMPOSE_CONVERT_WINDOWS_PATHS=1


## Test and verification

After containers are up and running, go to localhost:8000 (default) and you will see CMS Blue Button landing page,
follow documentation to create account, register applications, etc., note, on a local development environment, email might not be properly set, so confirmation email might not be received, and hence account activation needs to
be done manually by going to localhost:8000/admin and activate it.

Test from clients:


* Test from in browser testclient - from top of developer sandbox click link 'testclient'
* Test from CMS Blue Button Sample Clients:
  * Ruby on Rails Sample Client: [Blue Button Sample Client Rails](https://github.com/CMSgov/bluebutton-sample-client-rails) 
  * Django Sample Client: [Blue Button Sample Client Django](https://github.com/CMSgov/bluebutton-sample-client-django)

Make changes to configurations following sample clients instructions and test the end to end scenarios.

## Remote debugging blue button server
## add to .env below environment variable for bb20 container

BB20_ENABLE_REMOTE_DEBUG=true

## Start blue button server

```
cd <cms_projects_base_dir>/bluebutton-web-server/dev-local
docker-compose up -d bb20

```
## After bb20 is up and running, ptvsd is listening on port 5678,
## attach to bb20 from IDE, e.g. VSCode and put break points on execution path, and debugging.


## Remote debugging blue button server unit tests

```
cd <cms_projects_base_dir>/bluebutton-web-server/dev-local
docker-compose up -d bb20tests

```
## docker-compose up -d bb20tests starts with ptvsd wait on port 6789 for debugger to attach,
## attach to bb20tests from IDE, e.g. VSCode and put break points in test cases, and debugging.

```
docker-compose up -d bb20tests

```
make sure tests are waiting on 6789:

.....................
dev-local_bb20tests_1   python3 -m ptvsd --host 0. ...   Up      0.0.0.0:6789->6789/tcp

