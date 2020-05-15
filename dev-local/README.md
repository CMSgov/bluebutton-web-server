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




