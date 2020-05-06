# Docker Compose

## BFD
The bfd system needs a few variables to be set:
- `BFD_DIR` specifies the directory on your host machine where you have cloned https://github.com/CMSgov/beneficiary-fhir-data
- (optional) `SYNTHETIC_DATA` specifies a folder where you have the full set of synthetic rif files.
- (defaults to `/app`) `BFD_MOUNT_POINT` the path within the service container where the beneficiary-fhir-data directory will be mounted.

Here's an example `.env` file that docker-compose could use:
```
BFD_DIR=../beneficiary-fhir-data
SYNTHETIC_DATA=../synthetic-data
```

```
docker-compose up -d bfd
docker-compose logs -f | grep bfd_1
docker-compose exec bfd make load
```

## bb 2.0 specific
```
docker-compose up -d bb20
docker-compose exec bb20 ./docker-compose/migrate.sh
```

update [bb20 resource router](http://localhost:8000/admin/server/resourcerouter/1/change/) `https://bfd.local:9954`


# Vagrant

## Notes:

the directory structure this assumes:

- Vagrantfile
- Makefile
- allow_local_port_config.patch 
- beneficiary-fhir-data/

### spinup
```
cd beneficiary-fhir-data
git apply ../allow_local_port_config.patch
cd ..
vagrant up
```
```
vagrant ssh
cd /vagrant
make run
```

### Populate a very small amount of data (server must be running)

### Apply the patch
This causes the `bfd-pipeline-rfi-load` integration test to persist `SAMPLE_A` and `SAMPLE_U` to the hsql database
```
cd beneficiary-fhir-data
git apply ../load_data.patch
```
### Set the correct database port
The only way I've found to do this is to `ack` for `jdbc:hsqldb:hsql`:
```
ack jdbc:hsqldb:hsql
```
That returns a few results, the one you want is from `beneficiary-fhir-data/apps/bfd-server/bfd-server-war/target/server-work/server-console.log` and should look something like:
```
38:{"timestamp":"2019-10-24T13:20:35.483+0000","level":"DEBUG","thread":"main","logger":"com.zaxxer.hikari.HikariConfig","message":"jdbcUrl.........................jdbc:hsqldb:hsql://localhost:45269/test-embedded","context":"default"}
56:{"timestamp":"2019-10-24T13:20:35.499+0000","level":"DEBUG","thread":"main","logger":"com.zaxxer.hikari.util.DriverDataSource","message":"Loaded driver with class name org.hsqldb.jdbc.JDBCDriver for jdbcUrl=jdbc:hsqldb:hsql://localhost:45269/test-embedded","context":"default"}
61:{"timestamp":"2019-10-24T13:20:35.777+0000","level":"INFO","thread":"main","logger":"org.flywaydb.core.internal.dbsupport.DbSupportFactory","message":"Database: jdbc:hsqldb:hsql://localhost:45269/test-embedded (HSQL Database Engine 2.4)","context":"default"}
```
In this case the port is `45269`. This is a random port generated [_within_ the database startup logic.](https://github.com/CMSgov/beneficiary-fhir-data/blob/master/apps/bfd-server/bfd-server-war/src/main/java/gov/cms/bfd/server/war/SpringConfiguration.java#L145)

Whatever port you find, replace the port on line 49 of `beneficiary-fhir-data/apps/bfd-pipeline/bfd-pipeline-rif-load/src/main/java/gov/cms/bfd/pipeline/rif/load/RifLoaderTestUtils.java` with the new port.


Now to load the data run:
```
cd beneficiary-fhir-data/apps/bfd-pipeline/bfd-pipeline-rif-load
mvn clean verify
```

After this is done you should be able to hit https://localhost:8080/v1/fhir/Patient/567834/?_format=json from your host machine and see that patients data!



