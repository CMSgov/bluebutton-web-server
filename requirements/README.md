## vendoring rqeuirements (2025-12-08)

```
make build
make generate
```

This will build a container in which we can run `pip-compile`, and then run `pip-compile` in that container.

### why?

We need to run `pip-compile` in a consistent environment, against a given version of `python` and `pip`. This lets us control that by controlling the version of Python in the container (for example). 

This leaves the outputs in the tree (`requirements.txt` and `requirements.dev.txt`), which are then used in the CI/CD build process (as well as `make build-local` when working locally).

### why?

We are no longer going to use the `vendor` directory. The `*.txt` files are versioned/SHA1'd, and therefore are "locked" to the version of the libraries we want to use. (And, downloads are checked against their SHAs.) Therefore, having the vendored artifacts is not necessary for build.

# prior documentation (pre 2025-12-08)

## Vendoring Python requirements

This process allows us to download requirements for the application and store them in the `vendor` directory so that they may be installed during the build process without requiring access to the internet to do so.

NOTE: the files in the `vendor` directory are meant to be used with `linux_x86_64` platforms.

### Steps to edit/update application requirements:

1. Edit the `requirements/requirements.in` file
2. Edit the `requirements/requirements.dev.in` file
3. From the project root, run `make reqs-compile reqs-download`
4. Add and commit changes to `requirements/requirements.in`, `requirements/requirements.dev.in`, `requirements/requirements.txt`, `requirements/requirements.dev.txt` and any new or updated modules in the `vendor` directory
5. Later, to install the requirements from the `vendor` directory, run: `make reqs-install`