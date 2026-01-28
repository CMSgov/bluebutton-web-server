## building requirements (post 2025-12-08)

The goal is to have a local environment that is consistent and repeatable (across dev machines, as we go to production, etc.). In order to consistently generate the requirements.txt/requirements.dev.txt files, a container for generating those files is provided.

### the short short how to update a library

1. Open the appropriate `.in` file
2. Remove the version pin for the library. E.g. change `urllib == 2.6.0` to `urllib`
3. Run `make generate`
4. Open the `.txt` file (e.g. `requirements.txt`)
5. Look at the version that the library was updated to
6. Copy that to the `.in` file, re-pinning the library (e.g. `urllib = 2.6.3`)

#### to test

1. `make build-local`
2. Run all unit tests (`make exec-web`, `python runtests.py`)
3. Run Selenium tests (`cd dev-local`, `make run-selenium ...`)

#### why?

What we are doing is being very explicit about what updates. In this way, only the library we want updated is allowed to update. There are two possible results:

1. **The library updates to the most recent version**. This is good. We're happy.
2. **The library does not update at all**. This means that there are constraints that prevent it from going higher. 

In that case, the approach is to unpin a second library, and then a third, until the *set* of library updates that are necessary are uncovered. We then re-pin all libraries and test.

### how to update requirements

1. make sure that the Python version for the build container matches what we are using in the development stack (/dev-local/Dockerfile.local), which in turn should match the Python version we ware using in production.
1. update the requriements.in (for production reqs) or requirements.dev.in (for local reqs)
1. `make generate`

The build invoked by `generate` provides a Linux container which is "pinned" to our local dev experience as well as the production environment. 

The `generate` sequence executes `pip-compile` inside the container. This way, regardless of the host machine a developer is using, it will compile the requirements against the correct Python version in an authentic production-like environment.

After generating `requirements.txt` and `requirements.dev.txt`, you will need to regenerate your local stack for development (`make build-local` from the top of the tree).

### why?

We need to run `pip-compile` in a consistent environment, against a given version of `python` and `pip`. This lets us maintain alignment with our production build process/environments.

This leaves the outputs in the tree (`requirements.txt` and `requirements.dev.txt`), which are then used in the CI/CD build process (as well as `make build-local` when working locally).

### why?

We are no longer going to use the `vendor` directory. The `*.txt` files are versioned/SHA1'd, and therefore are "locked" to the version of the libraries we want to use. (And, downloads are checked against their SHAs.) Therefore, having the vendored artifacts is not necessary for build.

# prior documentation (pre 2025-12-08)

*This documentation can be removed when we are confident in the process described above. -- 2025-12-09*

## Vendoring Python requirements

This process allows us to download requirements for the application and store them in the `vendor` directory so that they may be installed during the build process without requiring access to the internet to do so.

NOTE: the files in the `vendor` directory are meant to be used with `linux_x86_64` platforms.

### Steps to edit/update application requirements:

1. Edit the `requirements/requirements.in` file
2. Edit the `requirements/requirements.dev.in` file
3. From the project root, run `make reqs-compile reqs-download`
4. Add and commit changes to `requirements/requirements.in`, `requirements/requirements.dev.in`, `requirements/requirements.txt`, `requirements/requirements.dev.txt` and any new or updated modules in the `vendor` directory
5. Later, to install the requirements from the `vendor` directory, run: `make reqs-install`