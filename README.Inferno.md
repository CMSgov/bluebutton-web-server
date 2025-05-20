Run Inferno Test Kits
=====================================================
BB2 integration test suite include Inferno test kit(s)
(in this POC, picked Smart App Launch Test Kit for demo purpose, pull in as many inferno kits as needed by compliance requirement)

Setup
-----

At the base directory of the local repository, run below command to download, install, and start the inferno service

```bash
./docker-compose/start_inferno.sh
```

Run tests
----------

Run inferno tests (selenium based) against local BB2 (assuming it is already started), as below example:

```bash
./docker-compose/run_inferno_test_local.sh -p
```

For help:
```bash
./docker-compose/run_inferno_test_local.sh -h
```

Run inferno tests against remote BB2 (PROD, SBX, TEST) as below example:

```bash
./docker-compose/run_inferno_test_remote.sh -p TEST
```

For help:
```bash
./docker-compose/run_inferno_test_remote.sh -h
```
