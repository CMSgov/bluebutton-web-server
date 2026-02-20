# containers

docker run -v ./scripts:/home/boton/bb/ops/containers/bb-web-api/scripts -e TARGET_ENV=local --platform="linux/amd64" -t bb:latest

## structure

```
containers
  | - <application>
  |        | - files
  |        | - scripts
  |        | - Dockerfile
  |        | - Makefile
  | ...
```

### dockerfile 

Each application folder contains a Dockerfile specifying how to build a container that can be run locally or, in some cases, in production.

### makefile

The Makefile always provides two targets:

1. `build-local` for testing in a local stack
2. `build-production` for deployment to cloud environments

### scripts

Scripts external to the container---scripts that configure a local environment, for example---are in `scripts/external`. Scripts that are required inside the container as part of application execution are in `scripts/internal`.

### files

Files necessary to support the application---templates, etc.---are stored here.


## /tmp in the container

```
/tmp
|-- bfd
|   `-- certs
|       |-- cert.pem
|       `-- key.pem
`-- nginx
    |-- certs
    |   |-- cert.pem
    |   `-- key.pem
    |-- nginx.conf
    |-- tmp
    `-- uwsgi_params -> /etc/nginx/uwsgi_params
```